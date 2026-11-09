# Лабораторна робота №6
## Логування, моніторинг та rollback у ROS 2 системі

Підготовка середовища та перевірка пакетів
Активуємо базове середовище ROS 2 Humble та робочий простір, перевіряємо наявність потрібних пакетів, активних нод і топіків:

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
source install/setup.bash
pwd
ros2 pkg list | grep -E 'sensor_node_pkg|motion_control|robot_gui'
ros2 node list
ros2 topic list
```

Перевірка Git та поточного коду
Спершу перевіряємо, чи не налаштований Git раніше, і переглядаємо поточний код пакета `sensor_node_pkg`:

```bash
cd ~/ros2_ws/src/sensor_node_pkg

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Git-репозиторій уже існує"
    git status --short
else
    echo "Git-репозиторію ще немає"
fi

sed -n '1,180p' setup.py
sed -n '1,240p' sensor_node_pkg/sensor_node.py
```

Резервна копія
Перед зміною коду створюємо резервну копію файлу ноди:

```bash
cd ~/ros2_ws/src/sensor_node_pkg
cp sensor_node_pkg/sensor_node.py sensor_node.py.backup
ls -l sensor_node_pkg/sensor_node.py sensor_node.py.backup
```

Реалізація логування та heartbeat (sensor_node.py)
Нода `sensor_node` імітує датчик відстані, публікує дані у `/sensor_data` з частотою 10 Гц і застосовує ковзне середнє по 5 останніх вимірюваннях. Додатково окремий таймер щосекунди публікує сигнал активності (heartbeat) у топік `/heartbeat` (тип `std_msgs/msg/String`).

Реалізовано три рівні логування:
INFO - запуск ноди, значення Raw / Filtered, відправка heartbeat 
WARN - `Obstacle too close!`, коли фільтроване значення нижче порога 0.4 м 
ERROR - тестова імітація збою датчика `TEST ERROR` на 60-му циклі (≈ 6 с) 

Відкриваємо файл (ми маємо бути в папці `~/ros2_ws/src/sensor_node_pkg`):

```bash
nano sensor_node_pkg/sensor_node.py
```

Видаляємо старий код і вставляємо новий:

```Python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
import random


class SensorNode(Node):

    def __init__(self):
        super().__init__('sensor_node')

        # Publisher для даних датчика
        self.sensor_publisher = self.create_publisher(
            Float32, '/sensor_data', 10
        )

        # Publisher для heartbeat
        self.heartbeat_publisher = self.create_publisher(
            String, '/heartbeat', 10
        )

        # Таймер датчика: 10 Гц
        self.timer_period = 0.1
        self.timer = self.create_timer(
            self.timer_period, self.timer_callback
        )

        # Таймер heartbeat: 1 раз на секунду
        self.heartbeat_timer = self.create_timer(
            1.0, self.heartbeat_callback
        )

        self.heartbeat_count = 0
        self.cycle_count = 0

        # Буфер останніх 5 вимірювань
        self.window_size = 5
        self.data_history = []
        self.threshold = 0.4

        self.get_logger().info('Sensor Node started (10 Hz)')
        self.get_logger().info('Heartbeat monitoring enabled')

    def timer_callback(self):

        raw_distance = round(random.uniform(0.2, 1.2), 3)

        self.data_history.append(raw_distance)

        if len(self.data_history) > self.window_size:
            self.data_history.pop(0)

        filtered_distance = sum(self.data_history) / len(self.data_history)

        msg = Float32()
        msg.data = float(filtered_distance)
        self.sensor_publisher.publish(msg)

        self.cycle_count += 1

        self.get_logger().info(
            f'Raw: {raw_distance:.2f} m | Filtered: {filtered_distance:.2f} m'
        )

        if filtered_distance < self.threshold:
            self.get_logger().warning(
                f'Obstacle too close! Filtered: {filtered_distance:.2f} m'
            )

        # Імітація помилки для демонстрації ERROR
        if self.cycle_count == 60:
            self.get_logger().error(
                'TEST ERROR: simulated sensor fault'
            )

    def heartbeat_callback(self):

        self.heartbeat_count += 1

        msg = String()
        msg.data = f'ALIVE - heartbeat #{self.heartbeat_count}'

        self.heartbeat_publisher.publish(msg)

        self.get_logger().info(
            f'Heartbeat sent: {msg.data}'
        )


def main(args=None):

    rclpy.init(args=args)
    node = SensorNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info('Sensor Node stopped')

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Перевіряємо синтаксис:

```bash
python3 -m py_compile sensor_node_pkg/sensor_node.py
```

Збірка пакета
Переходимо в корінь робочого простору та збираємо лише наш пакет:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select sensor_node_pkg
source install/setup.bash
```

Запуск ноди (Термінал 1)

```bash
ros2 run sensor_node_pkg sensor_node
```

Повідомлення про запуск, значення `Raw` і `Filtered`, попередження `Obstacle too close` та через ≈ 6 секунд тестове `TEST ERROR`.

Моніторинг через heartbeat (Термінал 2)
Не закриваючи перший термінал, відкриваємо другий:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

Перевіряємо список топіків:

```bash
ros2 topic list
```

Прослуховуємо дані датчика:

```bash
ros2 topic echo /sensor_data
```

Прослуховуємо heartbeat (зупинка через `Ctrl + C`):

```bash
ros2 topic echo /heartbeat
```

Перевіряємо частоту heartbeat:

```bash
ros2 topic hz /heartbeat
```

Очікуваний результат ≈ `average rate: 1.0`, що підтверджує публікацію один раз на секунду.

Робота з Git (версіонування)
Зупиняємо ноду в першому терміналі через `Ctrl + C`, повертаємося до терміналу з файлами та переглядаємо вміст пакета:

```bash
cd ~/ros2_ws/src/sensor_node_pkg
ls -la
```

Ініціалізація репозиторію:

```bash
git init
```

Створюємо `.gitignore`, щоб не додавати тимчасові файли:

```bash
nano .gitignore
```

```text
__pycache__/
*.pyc
*.backup
```

Зберігаємо: `Ctrl + O` → `Enter` → `Ctrl + X`. Перевіряємо стан:

```bash
git status
```

Git повідомляє: `On branch master`, `No commits yet`, `Untracked files`. Резервна копія `sensor_node.py.backup` у списку відсутня, тож `.gitignore` працює.

Додаємо файли та перевіряємо, що саме додалося:

```bash
git add .
git status
```

У секції `Changes to be committed` має бути список файлів пакета. Створюємо стабільну версію:

```bash
git commit -m "Stable version"
```

Це перша контрольна точка, до якої ми повертаємося під час rollback. Перевіряємо її наявність:

```bash
git log --oneline
```

Реалізація rollback
Перевіряємо, чи може Git відновити програму після навмисного пошкодження коду.

Створюємо навмисну помилку
Переконуємося, що нода зупинена (`Ctrl + C`), і переходимо в папку пакета:

```bash
cd ~/ros2_ws/src/sensor_node_pkg
```

Додаємо в кінець Python-файлу незавершене оголошення функції (синтаксична помилка):

```bash
echo "def broken(" >> sensor_node_pkg/sensor_node.py
```

Перевіряємо, що код зламаний

```bash
python3 -m py_compile sensor_node_pkg/sensor_node.py
```

Очікуваний результат: повідомлення `SyntaxError`. Дивимося, які зміни бачить Git:

```bash
git status
```

Файл `sensor_node.py` відображається як змінений (`modified`).

Виконуємо rollback

```bash
git restore sensor_node_pkg/sensor_node.py
```

Команда повертає файл до останнього коміту, тобто до стабільної версії `Stable version`. Команду `git checkout HEAD~1` не використовуємо, оскільки в репозиторії лише один коміт і попереднього немає. Перевіряємо:

```bash
git status
```

Очікуваний результат:

```text
nothing to commit, working tree clean
```

Це означає, що зміни скасовано.

Фінальне тестування після rollback
Повторно збираємо пакет

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select sensor_node_pkg
source install/setup.bash
```

Запускаємо відновлену ноду (Термінал 1)

```bash
ros2 run sensor_node_pkg sensor_node
```

Нода знову виводить `Sensor Node started (10 Hz)`, `Heartbeat monitoring enabled`, повідомлення `Raw` і `Filtered`, попередження `Obstacle too close` та через ≈ 6 секунд `TEST ERROR`.

Перевіряємо моніторинг (Термінал 2, ноду не зупиняємо)

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 topic list
ros2 topic echo /sensor_data
ros2 topic echo /heartbeat
ros2 topic hz /heartbeat
```

Топіки `/heartbeat`, `/parameter_events`, `/rosout`, `/sensor_data` присутні, дані датчика надходять, heartbeat приходить приблизно раз на секунду (≈ 1.0 Hz).

Перевірка Git після завершення
Зупиняємо ноду в першому терміналі (`Ctrl + C`) та виконуємо:

```bash
cd ~/ros2_ws/src/sensor_node_pkg
git log --oneline
git status
```

Очікуваний результат:

```text
067634e Stable version

On branch master
nothing to commit, working tree clean
```

# Запуск програми

Збірка та запуск ноди

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select sensor_node_pkg
source install/setup.bash
ros2 run sensor_node_pkg sensor_node
```

Термінал 2: моніторинг

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 topic list
ros2 topic echo /heartbeat
ros2 topic hz /heartbeat
```

Rollback

```bash
cd ~/ros2_ws/src/sensor_node_pkg
echo "def broken(" >> sensor_node_pkg/sensor_node.py   # навмисна помилка
python3 -m py_compile sensor_node_pkg/sensor_node.py   # SyntaxError
git status                                             # modified
git restore sensor_node_pkg/sensor_node.py             # rollback
git status                                             # working tree clean
```
Перевіряємо, чи код відновився

```bash
python3 -m py_compile sensor_node_pkg/sensor_node.py
```
Якщо термінал нічого не вивів — чудово! Це означає, що синтаксичних помилок більше немає.

Перевіряємо роботу, перший термінал:
```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select sensor_node_pkg
source install/setup.bash
```

Запускаємо відновлену ноду:

```bash
ros2 run sensor_node_pkg sensor_node
```

У другому терміналі перевіряємо heartbeat:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 topic echo /heartbeat
```

Маємо знову побачити повідомлення ALIVE.

Це вже підтверджує, що після відновлення коду нода запускається та публікує повідомлення.
