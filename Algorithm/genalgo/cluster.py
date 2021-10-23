import random
import sys
  
# setting path
sys.path.append('../acopyClean')

import acopyClean

class Chromosome:
    def __init__(self, numberOfCrossoverPoints,
            mutationSize,
            crossoverProbability,
            mutationProbability,
            parentChromosome,
            setupOnly, matrix, address_params, machines, address_machines):
        if parentChromosome != None:
            if setupOnly == False:
                self.permutation = parentChromosome.permutation.copy()
                self.itog = parentChromosome.itog
                self.fitness = parentChromosome.fitness
                self.cluster_time = parentChromosome.cluster_time
                self.cluster_volume = parentChromosome.cluster_volume
            else:
                self.permutation = []
                for i in range(len(parentChromosome.address_params)):
                    while True:
                        value = random.randrange(len(parentChromosome.machines))
                        if parentChromosome.address_machines[i][value] == True:
                            self.permutation.append(value)
                            break
                self.itog = True
                self.fitness = 0
            self.matrix = parentChromosome.matrix
            self.numberOfCrossoverPoints = parentChromosome.numberOfCrossoverPoints
            self.mutationSize = parentChromosome.mutationSize
            self.crossoverProbability = parentChromosome.crossoverProbability
            self.mutationProbability = parentChromosome.mutationProbability
            self.address_params = parentChromosome.address_params
            self.machines = parentChromosome.machines
            self.address_machines = parentChromosome.address_machines
            self.count_elem = parentChromosome.count_elem
        else:
            self.numberOfCrossoverPoints = numberOfCrossoverPoints
            self.mutationSize = mutationSize
            self.crossoverProbability = crossoverProbability
            self.mutationProbability = mutationProbability
            self.matrix = matrix
            self.address_params = address_params
            self.machines = machines
            self.address_machines = address_machines
            self.permutation = []
            for i in range(len(address_params)):
                while True:
                    value = random.randrange(len(machines))
                    if address_machines[i][value] == True:
                        self.permutation.append(value)
                        break
            self.count_elem = len(self.permutation)
            self.itog = True
            self.fitness = 0
        if self.fitness == 0:
            self.calculateFitness()

    def calculateFitness(self):
        self.fitness = 0
        self.itog = True
        alpha = 0.001 # суммарное (среди всех кластеров) попарное расстояние внутри кластера
        beta = 0.001 # суммарный штраф по времени
        gamma = 0.001 # равномерность по времени
        delta = 0.001 # равномерность по объему в отношении к объемам машин
        epsilon = 0.001 # суммарное время пути
        data_for_cluster = []
        for i in range(len(self.machines)):
            data_for_cluster.append([])
        cluster_time = [0] * len(self.machines)
        cluster_volume = [0] * len(self.machines)
        for num, cluster in enumerate(self.permutation):
            if self.address_params[num]['count_orders'] > 0:
                data_for_cluster[cluster].append(num)
                cluster_time[cluster] += self.address_params[num]['time'] / 60
                cluster_volume[cluster] += self.address_params[num]['volume']
        for num, cluster in enumerate(data_for_cluster):
            if len(cluster) > 0:
                # solver = acopyClean.LiteSolver(rho=.01, q=1, iter_without_record=100000)
                # colony = acopyClean.LiteColony(alpha=1, beta=1.1)
                # G = acopyClean.LiteGrath(len(cluster))
                # for item in cluster:
                #     G.add_node(data = item)

                for i in range(len(cluster)):
                    for j in range(len(cluster)):
                        if i != j:
                            # G.add_edge(i,j, weight=self.matrix[cluster[i]][cluster[j]])
                            alpha += self.matrix[cluster[i]][cluster[j]]

                # апельсин: Грубый метод подсчета задачи коммивояжера
                min_itog_distance = 1e8
                for k in range(len(cluster)):
                # for _ in range(max(int(len(cluster) / 5), 1)):
                    not_visited = set(cluster)
                    path = []
                    itog_distance = 0
                    random_start = k
                    # random_start = random.randrange(len(cluster))
                    not_visited.remove(cluster[random_start])
                    path.append(random_start)
                    for __ in range(len(cluster) - 1):
                        min_path = 1e8
                        min_index = -1
                        for i in not_visited:
                            if self.matrix[path[-1]][i] < min_path:
                                min_path = self.matrix[path[-1]][i]
                                min_index = i
                        not_visited.remove(min_index)
                        path.append(min_index)
                        itog_distance += min_path
                    min_itog_distance = min(min_itog_distance, itog_distance)
                # tour = solver.solve(G, colony, gen_size = 1, limit=50)
                epsilon += min_itog_distance
                # alpha += min_itog_distance + self.matrix[path[-1]][path[0]]
                cluster_time[num] += min_itog_distance / 3600
        # average_time = sum(cluster_time) / len(self.machines)
        sum_time_machines = sum(i['max_time'] - i['min_time'] for i in self.machines)
        percent_time_machines = [(i['max_time'] - i['min_time']) / sum_time_machines for i in self.machines]
        sum_cluster_time = sum(cluster_time)
        sum_volume_machines = sum(i['length']*i['width']*i['height'] for i in self.machines)
        percent_volume_machines = [i['length']*i['width']*i['height'] / sum_volume_machines for i in self.machines]
        sum_cluster_volume = sum(cluster_volume)
        for i in range(len(self.machines)):
            if (self.machines[i]['max_time'] - self.machines[i]['min_time']) - cluster_time[i] < 0:
                beta += cluster_time[i] - (self.machines[i]['max_time'] - self.machines[i]['min_time'])
                self.itog = False
            gamma += abs(percent_time_machines[i] - (cluster_time[i] / sum_cluster_time))
            # gamma += abs(average_time - cluster_time[i])
            delta += abs(percent_volume_machines[i] - (cluster_volume[i] / sum_cluster_volume))
        # self.fitness = ((alpha / 3600) ** 2) * (beta ** 8) * (gamma ** 1.6) * ((delta * 10) ** 1) * ((epsilon / 3600) ** 6.4)
        # self.fitness = ((alpha / 3600) ** 64) * (beta ** 80) * (gamma ** 1) * ((delta * 10) ** 1) * ((epsilon / 3600) ** 64)
        # self.fitness = ((alpha / 3600) ** 32) * (beta ** 80) * (gamma ** 2) * ((delta * 10) ** 1) * ((epsilon / 3600) ** 32)
        self.fitness = ((alpha / 3600) ** 32) * (beta ** 80) * ((gamma * 10) ** 2) * ((delta * 10) ** 1) * ((epsilon / 3600) ** 32)
        self.fitness = - self.fitness
        self.cluster_time = cluster_time
        self.cluster_volume = cluster_volume
    
    def crossover(self, other):
        if random.randrange(100) > self.crossoverProbability:
            return Chromosome(None, None, None, None, self, False, None, None, None, None)
        
        newChromosome = Chromosome(None, None, None, None, self, True, None, None, None, None)

        # определить точку пересечения (случайным образом)
        cp = [False] * self.count_elem

        points = [0, self.count_elem]
        for i in range(self.numberOfCrossoverPoints):
            while True:
                p = random.randrange(self.count_elem)
                if cp[p] == False:
                    cp[p] = True
                    points.append(p)
                    break
        points.sort()

        first = random.randrange(2) == 0
        newPermutation = []
        for num, point in enumerate(points):
            if num == len(points) - 1:
                break
            if first:
                newPermutation.extend(self.permutation[point:points[num + 1]])
            else:
                newPermutation.extend(other.permutation[point:points[num + 1]])
            first = not first
        
        newChromosome.permutation = newPermutation
        # newChromosome.calculateFitness()
        
        return newChromosome
    
    def mutation(self):
        if random.randrange(100) > self.mutationProbability:
            return

        for i in range(self.mutationSize):
            point = random.randrange(self.count_elem)
            while True:
                value = random.randrange(len(self.machines))
                if self.address_machines[point][value] == True:
                    self.permutation[point] = value
                    break

        # self.calculateFitness()

class GenAlgo:

    def __init__(self, numberOfChromosomes, replaceByGeneration, trackBest, prototype):
        
        self.replaceByGeneration = replaceByGeneration
        self.currentBestSize = 0
        self.currentGeneration = 0

        self.prototype = prototype

        if numberOfChromosomes < 2:
            numberOfChromosomes = 2

        if trackBest < 1:
            trackBest = 1
        
        if self.replaceByGeneration < 1:
            self.replaceByGeneration = 1
        elif self.replaceByGeneration > numberOfChromosomes - trackBest:
            self.replaceByGeneration = numberOfChromosomes - trackBest
        
        self.chromosomes = [None] * numberOfChromosomes
        self.bestFlags = [False] * numberOfChromosomes
        self.bestChromosomes = [None] * trackBest

    def getBestChromosome(self):
        return self.chromosomes[self.bestChromosomes[0]]

    def getAllBestIndexes(self):
        no_best_indexes = []
        best_indexes = []
        for index in range(len(self.bestFlags)):
            if self.bestFlags[index]:
                best_indexes.append(index)
            else:
                no_best_indexes.append(index)
        return best_indexes, no_best_indexes
        # return [index for index in range(len(self.bestFlags)) if self.bestFlags[index]]

    def isInBest(self, chromosomeIndex):
        return self.bestFlags[chromosomeIndex]

    def addToBest(self, chromosomeIndex):

        if (self.currentBestSize == len(self.bestChromosomes)
            and self.chromosomes[self.bestChromosomes[self.currentBestSize - 1]].fitness >=
                self.chromosomes[chromosomeIndex].fitness) or self.bestFlags[chromosomeIndex]:
            return

        searchIndex = self.currentBestSize
        for i in range(self.currentBestSize, -1, -1):
            searchIndex = i
            if i <= 0:
                break
            if i < len(self.bestChromosomes):
                if self.chromosomes[self.bestChromosomes[i - 1]].fitness > self.chromosomes[chromosomeIndex].fitness:
                    break
                
                self.bestChromosomes[i] = self.bestChromosomes[i - 1]
            else:
                self.bestFlags[self.bestChromosomes[i - 1]] = False

        self.bestChromosomes[searchIndex] = chromosomeIndex
        self.bestFlags[chromosomeIndex] = True

        if self.currentBestSize < len(self.bestChromosomes):
            self.currentBestSize += 1


    def start(self):

        if not self.prototype:
            return
        for i, item in enumerate(self.chromosomes):
            if item !=None:
                self.chromosomes[i] = None
            self.chromosomes[i] = Chromosome(None, None, None, None, self.prototype, True, None, None, None, None)
            self.addToBest(i)
        self.currentGeneration = 0

        while self.currentGeneration < 8000:

            # if self.currentGeneration < 1000 and self.currentGeneration % 100 == 0:
            #     print(self.currentGeneration)
            #     print(self.getBestChromosome().fitness)

            # if self.currentGeneration > 1 and self.currentGeneration % 1000 == 0:
            #     print(self.currentGeneration)
            #     print(self.getBestChromosome().fitness)

            offspring = [None] * self.replaceByGeneration
            best_indexes, no_best_indexes = self.getAllBestIndexes()
            for j, item in enumerate(offspring):

                # randIndex = random.randrange(len(self.chromosomes))
                # while True:
                #     randIndex2 = random.randrange(len(self.chromosomes))
                #     if randIndex != randIndex2:
                #         break

                # offspring[j] = self.chromosomes[randIndex].crossover(self.chromosomes[randIndex2])
                # offspring[j].mutation()
                # offspring[j].calculateFitness()
                if j < len(offspring) / 3:
                    randIndex = random.randrange(len(best_indexes))
                    while True:
                        randIndex2 = random.randrange(len(best_indexes))
                        if randIndex != randIndex2:
                            break
                    offspring[j] = self.chromosomes[best_indexes[randIndex]].crossover(self.chromosomes[best_indexes[randIndex2]])
                elif j < len(offspring) - (len(offspring) / 3):
                    randIndex = random.randrange(len(best_indexes))
                    randIndex2 = random.randrange(len(no_best_indexes))
                    offspring[j] = self.chromosomes[best_indexes[randIndex]].crossover(self.chromosomes[no_best_indexes[randIndex2]])
                else:
                    randIndex = random.randrange(len(no_best_indexes))
                    while True:
                        randIndex2 = random.randrange(len(no_best_indexes))
                        if randIndex != randIndex2:
                            break
                    offspring[j] = self.chromosomes[no_best_indexes[randIndex]].crossover(self.chromosomes[no_best_indexes[randIndex2]])
                
                offspring[j].mutation()
                offspring[j].calculateFitness()
            for j in range(self.replaceByGeneration):
                ci = random.randrange(len(self.chromosomes))
                while self.isInBest(ci):
                    ci = random.randrange(len(self.chromosomes))
                
                # if offspring[j].fitness >= self.chromosomes[ci].fitness:
                self.chromosomes[ci] = offspring[j]
                self.addToBest(ci)

            self.currentGeneration += 1

