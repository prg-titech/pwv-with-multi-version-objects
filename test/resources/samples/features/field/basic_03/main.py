from log import Log
def main():
    log = Log()
    print(log.log)
    log.new_method()
    print(log.log)
    log.legacy_method()
    print(log.log)

if __name__ == "__main__":
    main()
