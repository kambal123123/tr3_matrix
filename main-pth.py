import multiprocessing  # Для создания и управления процессами
import random  # Для генерации случайных чисел
import time  # Для эмуляции задержек
import sys  # Для работы с аргументами командной строки
import threading  # Для запуска отдельного потока пользовательского ввода
import queue  # Для обработки исключения пустой очереди
import signal  # Для перехвата системных сигналов прерывания

def create_random_square_matrix(dim):
    """
    Создает квадратную матрицу размером dim x dim, заполненную случайными числами от 0 до 10.
    """
    matrix = []
    for _ in range(dim):
        row = [random.randint(0, 10) for _ in range(dim)]
        matrix.append(row)
    return matrix

def producer_matrix_pair(matrix_queue, dimension, termination_event):
    """
    Процесс-генератор: создает пары случайных матриц и помещает их в очередь.
    При получении сигнала остановки завершает работу.
    """
    print("Процесс генерации матриц запущен.")
    try:
        while not termination_event.is_set():
            mat1 = create_random_square_matrix(dimension)
            mat2 = create_random_square_matrix(dimension)
            matrix_queue.put((mat1, mat2))
            print("Пара матриц сгенерирована и отправлена.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Процесс генератора матриц прерван пользователем.")
    finally:
        # Отправляем в очередь сигнал для завершения потребителя
        matrix_queue.put(None)
        print("Процесс генерации матриц завершен.")

def consumer_matrix_multiply(matrix_queue, termination_event):
    """
    Процесс-потребитель: получает пары матриц из очереди, перемножает их и сохраняет результаты в файл.
    Останавливается при получении сигнала остановки и пустой очереди.
    """
    print("Процесс умножения матриц запущен.")
    try:
        with open('multiplication_results.txt', 'w', encoding='utf-8') as outfile:
            while True:
                if termination_event.is_set() and matrix_queue.empty():
                    break
                try:
                    matrices = matrix_queue.get(timeout=1)
                except queue.Empty:
                    continue
                if matrices is None:
                    print("Получен сигнал остановки от генератора.")
                    break
                matA, matB = matrices
                if len(matA[0]) != len(matB):
                    print("Ошибка: несовместимые размеры матриц для умножения.")
                    continue
                product = multiply_square_matrices(matA, matB)
                save_matrix_to_file(product, outfile)
                print("Матрицы перемножены и результат записан.")
    except KeyboardInterrupt:
        print("Процесс умножения прерван пользователем.")
    finally:
        print("Процесс умножения матриц завершен.")

def multiply_square_matrices(A, B):
    """
    Выполняет умножение двух квадратных матриц A и B.
    Возвращает результат в виде новой матрицы.
    """
    n_rows = len(A)
    n_cols = len(B[0])
    result = [[0] * n_cols for _ in range(n_rows)]
    for i in range(n_rows):
        for j in range(n_cols):
            for k in range(len(B)):
                result[i][j] += A[i][k] * B[k][j]
    return result

def save_matrix_to_file(matrix, file_object):
    """
    Записывает матрицу в файл, построчно.
    Добавляет разделитель после каждой матрицы.
    """
    for row in matrix:
        file_object.write(' '.join(map(str, row)) + '\n')
    file_object.write('-' * 30 + '\n')

def monitor_user_input(stop_event):
    """
    Поток, ожидающий ввода команды 'stop' для завершения работы программы.
    """
    while not stop_event.is_set():
        try:
            user_command = input("Введите 'stop' для завершения программы: ").strip().lower()
            if user_command == 'stop':
                stop_event.set()
                print("Получена команда остановки. Завершение работы.")
                break
        except EOFError:
            break
        except KeyboardInterrupt:
            stop_event.set()
            print("\nРабота прервана пользователем.")
            break

def handle_interrupt_signal(signum, frame):
    """
    Обработчик системного сигнала прерывания (Ctrl+C).
    """
    print("\nСигнал прерывания получен. Инициация завершения.")
    global stop_event
    stop_event.set()

def main():
    global stop_event
    stop_event = multiprocessing.Event()

    signal.signal(signal.SIGINT, handle_interrupt_signal)

    if len(sys.argv) != 2:
        print("Использование: python <название_скрипта>.py <размер_матрицы>")
        sys.exit(1)

    try:
        matrix_dim = int(sys.argv[1])
        if matrix_dim <= 0:
            raise ValueError
    except ValueError:
        print("Размер матрицы должен быть положительным целым числом.")
        sys.exit(1)

    mat_queue = multiprocessing.Queue()

    generator_proc = multiprocessing.Process(target=producer_matrix_pair, args=(mat_queue, matrix_dim, stop_event))
    multiplier_proc = multiprocessing.Process(target=consumer_matrix_multiply, args=(mat_queue, stop_event))

    generator_proc.start()
    multiplier_proc.start()

    input_thread = threading.Thread(target=monitor_user_input, args=(stop_event,))
    input_thread.start()

    input_thread.join()
    generator_proc.join()
    multiplier_proc.join()

    print("Все процессы завершены. Программа успешно закрыта.")

if __name__ == "__main__":
    main()
