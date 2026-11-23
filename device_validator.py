
"""
Лабораторна робота № 9. Модуль 2.
Модуль багаторівневої валідації параметрів контролера USB 3.2,
ланцюжків винятків (raise from) та профілювання надійності.
Освітній компонент: Програмування на Python.
Варіант 20.
"""

import sys
import time
from typing import Dict, Any

from custom_exceptions import (
    USBSubsystemError,
    VBUSOverCurrentError,
    MaxPacketSizeInvalidError,
)


def validate_usb_configuration(config: Dict[str, Any]) -> bool:
    """
    Здійснює комплексну валідацію словника конфігурації USB 3.2.
    Перевіряє струм порту, розмір пакета та кількість кінцевих точок.
    """

    # 1. Валідація наявності обов'язкових ключів
    required_keys = {"port_current_ma", "max_packet_size", "endpoint_count"}
    missing_keys = required_keys.difference(config.keys())

    if missing_keys:
        raise KeyError(
            f"У конфігураційній структурі відсутні обов'язкові параметри: {missing_keys}"
        )

    # 2. Валідація струму порту USB
    try:
        current_ma = float(config["port_current_ma"])
    except (ValueError, TypeError) as type_err:
        raise USBSubsystemError(
            "Параметр 'port_current_ma' повинен бути числовим значенням.",
            error_code=1003
        ) from type_err

    if current_ma < 0:
        raise USBSubsystemError(
            "Струм порту USB не може бути від'ємним.",
            error_code=1004
        )

    if current_ma > 900.0:
        raise VBUSOverCurrentError(current_ma, max_ma=900.0)

    # 3. Валідація розміру пакета
    packet_size = config["max_packet_size"]

    if type(packet_size) is not int:
        raise USBSubsystemError(
            "Розмір пакета повинен бути цілим числом.",
            error_code=1005
        )

    if packet_size not in (512, 1024):
        raise MaxPacketSizeInvalidError(
            packet_size, allowed_sizes=(512, 1024)
        )

    # 4. Валідація кількості кінцевих точок
    endpoint_count = config["endpoint_count"]

    if type(endpoint_count) is not int or endpoint_count <= 0:
        raise USBSubsystemError(
            "Кількість кінцевих точок повинна бути додатним цілим числом.",
            error_code=1006
        )

    return True


def run_fault_tolerance_testbench(test_configs: list[dict]) -> None:
    """
    Запускає тестовий стенд обробки конфігураційних наборів
    із розрахунком метрик відновлення після збоїв P_recovery.
    """
    header_sep = "=" * 90
    sub_sep = "-" * 90

    print(header_sep)
    print(f"{'ТЕСТУВАННЯ ВІДМОВОСТІЙКОСТІ КОНТРОЛЕРА USB 3.2':^90}")
    print(header_sep)

    successful_runs = 0
    handled_faults = 0
    total_configs = len(test_configs)

    for idx, cfg in enumerate(test_configs, start=1):
        print(f"\nТест #{idx:02d}: Тестування конфігурації -> {cfg}")

        try:
            result = validate_usb_configuration(cfg)

        except VBUSOverCurrentError as current_err:
            handled_faults += 1
            print(f"  [ПЕРЕХОПЛЕНО СПЕЦІАЛІЗОВАНО]: {current_err}")
            print("  -> Дія системи: Вимкнення живлення порту USB.")

        except MaxPacketSizeInvalidError as packet_err:
            handled_faults += 1
            print(f"  [ПЕРЕХОПЛЕНО СПЕЦІАЛІЗОВАНО]: {packet_err}")
            print("  -> Дія системи: Відхилення некоректного пакета.")

        except USBSubsystemError as usb_err:
            handled_faults += 1
            print(f"  [ПЕРЕХОПЛЕНО БАЗОВИЙ ВИНЯТОК]: {usb_err}")
            if usb_err.__cause__:
                print(
                    f"  -> Першопричина (Chained Cause): "
                    f"{type(usb_err.__cause__).__name__}: {usb_err.__cause__}"
                )

        except KeyError as key_err:
            handled_faults += 1
            print(f"  [ПЕРЕХОПЛЕНО СТАНДАРТНИЙ]: Відсутній ключ структури -> {key_err}")

        else:
            successful_runs += 1
            print("  [УСПІХ]: Конфігурація контролера USB 3.2 валідна.")

        finally:
            print(f"  [FINALLY]: Аудит тесту #{idx} завершено.")

    print("\n" + header_sep)
    print(f"{'ПІДСУМКОВІ МЕТРИКИ НАДІЙНОСТІ СИСТЕМИ':^90}")
    print(sub_sep)

    total_faults = total_configs - successful_runs
    p_recovery = (
        handled_faults / total_faults
        if total_faults > 0 else 1.0
    )

    print(f"  Всього оброблено тестових наборів:   {total_configs:>5d}")
    print(f"  Штатних успішних конфігурацій:        {successful_runs:>5d}")
    print(f"  Локалізованих та оброблених збоїв:    {handled_faults:>5d}")
    print(f"  Коефіцієнт програмного відновлення (P): {p_recovery * 100:.2f}%")
    print(header_sep + "\n")


def main() -> None:
    """Головна точка входу лабораторної роботи."""

    # Набір тестових даних із різними типами дефектів
    test_suite = [

        # Тест 1: Повністю коректна конфігурація
        {"port_current_ma": 800, "max_packet_size": 512, "endpoint_count": 4},

        # Тест 2: Перевищення допустимого струму порту
        {"port_current_ma": 950, "max_packet_size": 512, "endpoint_count": 4},

        # Тест 3: Недопустимий розмір пакета
        {"port_current_ma": 800, "max_packet_size": 256, "endpoint_count": 4},

        # Тест 4: Некоректна кількість кінцевих точок
        {"port_current_ma": 800, "max_packet_size": 512, "endpoint_count": 0},

        # Тест 5: Некоректний тип струму (рядкове сміття)
        {"port_current_ma": "CORRUPTED_VALUE", "max_packet_size": 1024, "endpoint_count": 8},

        # Тест 6: Відсутність обов'язкового ключа
        {"port_current_ma": 800, "max_packet_size": 512},

        # Тест 7: Коректна конфігурація на допустимих значеннях
        {"port_current_ma": 900, "max_packet_size": 1024, "endpoint_count": 8},
    ]

    t_start = time.perf_counter()
    run_fault_tolerance_testbench(test_suite)
    t_elapsed = time.perf_counter() - t_start

    print(f"Час виконання діагностичного тестбенчу: {t_elapsed * 1000:.3f} мс\n")


if __name__ == "__main__":
    main()
