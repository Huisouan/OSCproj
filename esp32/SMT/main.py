from smtcontroller import *
def main():
    controller = SmtController()
    
    while True:

        time.sleep(1)
        controller.process_command()



if __name__ == "__main__":
    main()