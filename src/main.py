from src.simulation import Simulation

if __name__ == "__main__":
    results = []

    # collect data
    servers_max = 8
    for i in range(1, servers_max + 1):
        print("Starting simulation with %d servers" % i)

        simulation = Simulation()
        avg_time = simulation.start(i)
        print("-------------------")
        print()

        results.append((i, avg_time))

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
