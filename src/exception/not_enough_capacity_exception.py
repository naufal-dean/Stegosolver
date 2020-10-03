class NotEnoughCapacityException(Exception):
    '''Exception when the data to be inserted is bigger than the max capacity'''

    def __init__(self, data_size, max_capacity):
        super.__init__(f'Maximum data capacity is {max_capacity}, got {data_size}')
