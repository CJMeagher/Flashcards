def check_integer(num):
    if num not in range(45, 68):
        raise NotInBoundsError
    return num


def error_handling(num):
    try:
        check_integer(num)
        print(num)
    except NotInBoundsError as err:
        print(err)
