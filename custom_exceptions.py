
"""
Лабораторна робота № 9. Модуль 1.
Ієрархія користувацьких класів винятків для системи
валідації контролера шини USB 3.2.
Освітній компонент: Програмування на Python.
Варіант 20.
"""

import time


class USBSubsystemError(Exception):
    """Базовий клас для всіх винятків конфігурації підсистеми USB."""
    def __init__(self, message: str, error_code: int = 1000):
        super().__init__(message)
        self.error_code = error_code
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        return f"[ERR-{self.error_code}] ({self.timestamp}) {super().__str__()}"


class VBUSOverCurrentError(USBSubsystemError):
    """Збуджується, коли струм порту USB перевищує допустимі 900 мА."""
    def __init__(self, current_ma: float, max_ma: float = 900.0):
        self.current_ma = current_ma
        self.max_ma = max_ma

        msg = (
            f"Струм порту USB {current_ma:.2f} мА перевищує "
            f"максимально допустиме значення {max_ma:.2f} мА."
        )
        super().__init__(msg, error_code=1001)


class MaxPacketSizeInvalidError(USBSubsystemError):
    """Збуджується, коли розмір пакета USB не відповідає допустимим значенням."""
    def __init__(self, packet_size: int, allowed_sizes: tuple = (512, 1024)):
        self.packet_size = packet_size
        self.allowed_sizes = allowed_sizes

        msg = (
            f"Розмір пакета {packet_size} байт є недопустимим. "
            f"Дозволені розміри: {allowed_sizes} байт."
        )
        super().__init__(msg, error_code=1002)
