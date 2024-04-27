def str_to_enum(str_enum_class, str_value: str, ignore_not_found: bool = False, enum_default=None):
    for key, member in str_enum_class.__members__.items():
        if str_value == member.value:
            return member
    if ignore_not_found:
        return enum_default
    raise ValueError(f"Invalid enum value: {str_value}")
