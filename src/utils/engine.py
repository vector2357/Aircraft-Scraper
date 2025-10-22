def engine_left_time(total_time: str, current_time: str) -> str:
    total_time_as_float = float(total_time.strip())
    current_time_as_float = float(current_time.strip())

    result = total_time_as_float - current_time_as_float

    return f"{result:.2f}"