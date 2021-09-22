import numpy as np
import random
from Instance_Generator import Processing_time,A,D,M_num,Op_num,J,O_num,J_num
from Object_for_FJSP import Object

class Situation:
    def __init__(self,J_num,M_num,O_num,J,Processing_time,D,Ai):
        self.Ai=Ai                  #工件到达时间
        self.D=D                    #交货期
        self.O_num=O_num            #工序总数
        self.M_num=M_num            #机器数
        self.J_num=J_num            #工件数
        self.J=J                    #工件对应的工序数
        self.Processing_time = Processing_time   # 加工时间
        self.CTK=[0 for i in range(M_num)]      #各机器上最后一道工序的完工时间列表
        self.OP=[0 for i in range(J_num)]       #各工件的已加工工序数列表
        self.UK=[0 for i in range(M_num)]       #各机器的实际使用率
        self.CRJ=[0 for i in range(J_num)]      #工件完工率
        # 工件集：
        self.Jobs=[]
        for i in range(J_num):
            F=Object(i)
            self.Jobs.append(F)
        #机器集
        self.Machines = []
        for i in range(M_num):
            F = Object(i)
            self.Machines.append(F)

    #更新数据
    def _Update(self,Job,Machine):
        self.CTK[Machine]=max(self.Machines[Machine].End)
        self.OP[Job]+=1
        self.UK[Machine]=sum(self.Machines[Machine].T)/self.CTK[Machine]
        self.CRJ[Job]=self.OP[Job]/self.J[Job]

    #机器平均使用率
    def Features(self):

        #1 机器平均利用率
        U_ave=sum(self.UK)/self.M_num
        K=0
        for uk in self.UK:
            K+=np.square(uk-U_ave)
        #2 机器的使用率标准差
        U_std=np.sqrt(K/self.M_num)
        #3 平均工序完成率
        CRO_ave=sum(self.OP)/self.O_num
        #4 平均工件工序完成率
        CRJ_ave=sum(self.CRJ)/self.J_num
        K = 0
        for uk in self.CRJ:
            K += np.square(uk - CRJ_ave)
        #5 工件工序完成率标准差
        CRJ_std=np.sqrt(K/self.J_num)
        #6 Estimated tardiness rate Tard_e
        T_cur=sum(self.CTK)/self.M_num
        N_tard,N_left=0,0
        for i in range(self.J_num):
            if J[i]>self.OP[i]:
                N_left+=self.J[i]-self.OP[i]
                T_left=0
                for j in range(self.OP[i]+1,J[i]):
                    M_ij=[k for k in self.Processing_time[i][j] if k>0 or k<999]
                    T_left+=sum(M_ij)/len(M_ij)
                    if T_left+T_cur>self.D[i]:
                        N_tard+=self.J[i]-j+1
        try:
            Tard_e=N_tard/N_left
        except:
            Tard_e =9999
        #7 Actual tardiness rate Tard_a
        N_tard, N_left = 0, 0
        for i in range(self.J_num):
            if J[i] > self.OP[i]:
                N_left += self.J[i] - self.OP[i]
                try:
                    if self.CTK[i] > self.D[i]:
                        N_tard += self.J[i] - j
                except:
                    pass
        try:
            Tard_a = N_tard / N_left
        except:
            Tard_a =9999
        return U_ave,U_std,CRO_ave,CRJ_ave,CRJ_std,Tard_e,Tard_a

    #Composite dispatching rule 1
    #return Job,Machine
    def rule1(self):
        #T_cur:平均完工时间
        T_cur = sum(self.CTK) / self.M_num
        #Tard_Job:不能按期完成的工件
        Tard_Job=[i for i in range(self.J_num) if self.OP[i]<self.J[i] and self.D[i]<T_cur]
        UC_Job=[j for j in range(self.J_num) if self.OP[j]<self.J[j]]
        if Tard_Job==[]:
            Job_i=UC_Job[np.argmax([(self.D[i]-T_cur)/(self.J[i]-self.OP[i]) for i in UC_Job ])]
        else:
            T_ijave=[]
            for i in Tard_Job:
                Tad=[]
                for j in range(self.OP[i],self.J[i]):
                    T_ijk=[k for k in self.Processing_time[i][j] if k!=-1]
                    Tad.append(sum(T_ijk)/len(T_ijk))
                T_ijave.append(T_cur+sum(Tad)-self.D[i])
            Job_i=Tard_Job[np.argmax(T_ijave)]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij =self.Ai[Job_i]  # 工件i的arrival time
        A_ij = self.Ai[Job_i]  # 工件i的arrival time
        # print(A_ij)
        On = len(self.Jobs[Job_i].End)
        Mk = []
        for i in range(len(self.CTK)):
            if self.Processing_time[Job_i][On][i] != -1:
                C_ij+=self.Processing_time[Job_i][On][i]
                Mk.append(max(C_ij, A_ij, self.CTK[i]))
            else:
                Mk.append(9999)
        # print('This is from rule 1:',Mk)
        Machine=np.argmin(Mk)
        # print('This is from rule 1:',Machine)
        return Job_i,Machine

    #Composite dispatching rule 2
    #return Job,Machine
    def rule2(self):
        # T_cur:平均完工时间
        T_cur = sum(self.CTK) / self.M_num
        # Tard_Job:不能按期完成的工件
        Tard_Job = [i for i in range(self.J_num) if self.OP[i] < self.J[i] and self.D[i] < T_cur]
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        T_ijave = []
        for i in range(self.J_num):
            Tad = []
            for j in range(self.OP[i], self.J[i]):
                T_ijk = [k for k in self.Processing_time[i][j] if k != -1]
                Tad.append(sum(T_ijk) / len(T_ijk))
            T_ijave.append(sum(Tad))
        if Tard_Job==[]:
            Job_i=UC_Job[np.argmin([(self.D[i]-T_cur)/T_ijave[i] for i in UC_Job])]
        else:
            Job_i=Tard_Job[np.argmax([T_cur+T_ijave[i]-self.D[i] for i in Tard_Job ])]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij =self.Ai[Job_i]  # 工件i的arrival time
        A_ij = self.Ai[Job_i]  # 工件i的arrival time
        # print(A_ij)
        On = len(self.Jobs[Job_i].End)
        Mk = []
        for i in range(len(self.CTK)):
            if self.Processing_time[Job_i][On][i] != -1:
                C_ij+=self.Processing_time[Job_i][On][i]
                Mk.append(max(C_ij, A_ij, self.CTK[i]))
            else:
                Mk.append(9999)
        # print('This is from rule 2:',Mk)
        Machine = np.argmin(Mk)
        # print('This is from rule 2:',Machine)
        return Job_i,Machine

    #Composite dispatching rule 3
    def rule3(self):
        # T_cur:平均完工时间
        T_cur = sum(self.CTK) / self.M_num
        # Tard_Job:不能按期完成的工件
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        T_ijave = []
        for i in UC_Job:
            Tad = []
            for j in range(self.OP[i], self.J[i]):
                T_ijk = [k for k in self.Processing_time[i][j] if k != -1]
                Tad.append(sum(T_ijk) / len(T_ijk))
            T_ijave.append(T_cur + sum(Tad) - self.D[i])
        Job_i = UC_Job[np.argmax(T_ijave)]
        On = len(self.Jobs[Job_i].End)
        if random.random()<0.5:
            U=[]
            for i in range(len(self.UK)):
                if self.Processing_time[Job_i][On][i]==-1:
                    U.append(9999)
                else:
                    U.append(self.UK[i])
            Machine=np.argmin(U)
        else:
            MT=[]
            for j in range(self.M_num):
                if self.Processing_time[Job_i][On][j]==-1:
                    MT.append(9999)
                else:
                    MT.append(sum(self.Machines[j].T))
            Machine=np.argmin(MT)
        # print('This is from rule 3:',Machine)
        return Job_i,Machine

    #Composite dispatching rule 4
    def rule4(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Job_i= random.choice(UC_Job)
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij =self.Ai[Job_i]  # 工件i的arrival time
        A_ij = self.Ai[Job_i]  # 工件i的arrival time
        On = len(self.Jobs[Job_i].End)
        Mk = []
        for i in range(len(self.CTK)):
            if self.Processing_time[Job_i][On][i] != -1:
                C_ij+=self.Processing_time[Job_i][On][i]
                Mk.append(max(C_ij, A_ij, self.CTK[i]))
            else:
                Mk.append(9999)
        # print('This is from rule 4:',Mk)
        Machine = np.argmin(Mk)
        # print('This is from rule 4:',Machine)
        return Job_i,Machine

    #Composite dispatching rule 5
    def rule5(self):

        # T_cur:平均完工时间
        T_cur = sum(self.CTK) / self.M_num
        # Tard_Job:不能按期完成的工件
        Tard_Job = [i for i in range(self.J_num) if self.OP[i] < self.J[i] and self.D[i] < T_cur]
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        if Tard_Job==[]:
            Job_i=UC_Job[np.argmin([self.CRJ[i]*(self.D[i]-T_cur) for i in UC_Job])]
        else:
            T_ijave = []
            for i in Tard_Job:
                Tad = []
                for j in range(self.OP[i], self.J[i]):
                    T_ijk = [k for k in self.Processing_time[i][j] if k != -1]
                    Tad.append(sum(T_ijk) / len(T_ijk))
                T_ijave.append(1/(self.CRJ[i]+1)*(T_cur + sum(Tad) - self.D[i]))
            Job_i = Tard_Job[np.argmax(T_ijave)]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij =self.Ai[Job_i]  # 工件i的arrival time
        A_ij = self.Ai[Job_i]  # 工件i的arrival time
        On = len(self.Jobs[Job_i].End)
        Mk = []
        for i in range(len(self.CTK)):
            if self.Processing_time[Job_i][On][i] != -1:
                C_ij+=self.Processing_time[Job_i][On][i]
                Mk.append(max(C_ij, A_ij, self.CTK[i]))
            else:
                Mk.append(9999)
        # print('This is from rule 5:',Mk)
        Machine = np.argmin(Mk)
        # print('This is from rule 5:',Machine)
        return Job_i, Machine

    #Composite dispatching rule 6
    #return Job,Machine
    def rule6(self):
        # T_cur:平均完工时间
        T_cur = sum(self.CTK) / self.M_num
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        T_ijave = []
        for i in UC_Job:
            Tad = []
            for j in range(self.OP[i], self.J[i]):
                T_ijk = [k for k in self.Processing_time[i][j] if k != -1]
                Tad.append(sum(T_ijk) / len(T_ijk))
            T_ijave.append(T_cur + sum(Tad) - self.D[i])
        Job_i = UC_Job[np.argmax(T_ijave)]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij =self.Ai[Job_i]  # 工件i的arrival time
        A_ij = self.Ai[Job_i]  # 工件i的arrival time
        On = len(self.Jobs[Job_i].End)
        Mk = []
        for i in range(len(self.CTK)):
            if self.Processing_time[Job_i][On][i] != -1:
                C_ij+=self.Processing_time[Job_i][On][i]
                Mk.append(max(C_ij, A_ij, self.CTK[i]))
            else:
                Mk.append(9999)
        Machine = np.argmin(Mk)
        # print('this is from rule 6:',Mk)
        # print('This is from rule 6:',Machine)
        return Job_i,Machine

    def scheduling(self,action):
        Job,Machine=action[0],action[1]
        O_n=len(self.Jobs[Job].End)
        # print(Job, Machine,O_n)
        Idle=self.Machines[Machine].idle_time()
        try:
            last_ot=max(self.Jobs[Job].End)         #上道工序加工时间
        except:
            last_ot=0
        try:
            last_mt=max(self.Machines[Machine].End) #机器最后完工时间
        except:
            last_mt=0
        Start_time=max(last_ot,last_mt)
        PT=self.Processing_time[Job][O_n][Machine]    #工序加工时间
        for i in range(len(Idle)):
            if Idle[i][1]-Idle[i][0]>PT:
                if Idle[i][0]>last_ot:
                    start_time=Idle[i][0]
                    pass
                if Idle[i][0]<last_ot and Idle[i][1]-last_ot>PT:
                    start_time=last_ot
                    pass
        end_time=Start_time+PT
        self.Machines[Machine]._add(Start_time,end_time,Job,PT)
        self.Jobs[Job]._add(Start_time,end_time,Machine,PT)
        self._Update(Job,Machine)

    def reward(self,Ta_t,Te_t,Ta_t1,Te_t1,U_t,U_t1):
        '''
               :param Ta_t: Tard_a(t)
               :param Te_t: Tard_e(t)
               :param Ta_t1: Tard_a(t+1)
               :param Te_t1: Tard_e(t+1)
               :param U_t: U_ave(t)
               :param U_t1: U_ave(t+1)
               :return: reward
        '''
        if Ta_t1<Ta_t:
           rt=1
        else:
            if Ta_t1>Ta_t:
                rt=-1
            else:
                if Te_t1<Te_t:
                    rt=1
                else:
                    if Te_t1>Te_t:
                        rt=1
                    else:
                        if U_t1>U_t:
                            rt=1
                        else:
                            if U_t1>0.95*U_t:
                                rt=0
                            else:
                                rt=-1
        return rt

Sit=Situation(J_num,M_num,O_num,J,Processing_time,D,A)
