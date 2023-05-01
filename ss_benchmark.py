from perception.Perception import Perception
import time
import matplotlib.pyplot as plt

p = Perception()


def measure_ss_time():
    last_time = time.time()
    p.get_screenshot()
    return time.time() - last_time


times = []
avg = 0
n = 1000
for i in range(n):
    times.append(measure_ss_time())
    avg += times[len(times) - 1]/n
n, bins, patches = plt.hist(x=times, bins='auto', color='#0504aa',
                            alpha=0.7, rwidth=0.85)
plt.grid(axis='y', alpha=0.75)
plt.xlabel('Value (s)')
plt.ylabel('Frequency')
plt.title('Histogram')
plt.text(23, 45, r'$\mu=15, b=3$')
plt.show()
print(f"Average time: {avg}")
