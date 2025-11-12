import argparse
import time

def main():
    # создаём парсер аргументов
    parser = argparse.ArgumentParser(description="Example script with arguments.")

    # добавляем один аргумент --text
    parser.add_argument(
        "--mode",
        type=str,
        default="Hi",
        help="Every second output this text",
    )

    # разбираем аргументы из командной строки
    args = parser.parse_args()

    print(f"Running. Arg: {args.mode!r}. Output every second.")

    # бесконечный цикл
    while True:
        print(args.mode)
        time.sleep(1)


if __name__ == "__main__":
    main()