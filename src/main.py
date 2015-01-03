import multiprocessing
from multiprocessing.pool import Pool
from src.simulation import Simulation
from functools import reduce
from src.util import reporter


def experiment(servers_count):
        print("Starting simulation with %d servers" % servers_count)

        simulation = Simulation()
        avg_time = simulation.start(servers_count)
        print("-------------------")
        print()

        return servers_count, avg_time

if __name__ == "__main__":
    results = []

    # collect data
    servers_max = 8
    replications_count = 10

    p = Pool(multiprocessing.cpu_count())

    for i in range(0, replications_count):
        current_results = p.map(experiment, range(1, servers_max + 1))
        results.append(current_results)

    results = map(
        lambda el: reduce(
            lambda a, b: (a[0], a[1] + b[1]),
            el),
        zip(*results))

    results = list(map(lambda el: (el[0], el[1]/replications_count), results))

    print("-------------------")
    print("Collected results: ", results)

    # minimization

    # normalize
    time_max = max(map(lambda el: el[1], results))

    normalized_results\
        = list(map(lambda el: el[0]/servers_max + el[1]/time_max, results))

    # find minimum
    min_id = 0
    min_value = normalized_results[0]

    for i, el in enumerate(normalized_results):
        if el < min_value:
            min_value = el
            min_id = i

    print("-------------------")
    print("Experiment results:")
    print(results[min_id])

    reporter.save_report(results, results[min_id])