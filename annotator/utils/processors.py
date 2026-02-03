from annotator.structured import Subtasks
import re

def validate_time_format(time_str: str) -> bool:
    """
    Validates that a time string is in the correct format.
    
    Args:
        time_str: Time string to validate
        
    Returns:
        True if the format is valid (MM:SS or HH:MM:SS), False otherwise
    """
    pattern_mm_ss = r'^\d{1,2}:\d{2}$'
    pattern_hh_mm_ss = r'^\d{1,2}:\d{2}:\d{2}$'
    return bool(re.match(pattern_mm_ss, time_str) or re.match(pattern_hh_mm_ss, time_str))

def time_to_seconds(time_str: str) -> int:
    parts = time_str.split(":")
    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        if seconds >= 60:
            raise ValueError(f"Seconds must be less than 60: {time_str}")
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        if minutes >= 60 or seconds >= 60:
            raise ValueError(f"Minutes and seconds must be less than 60: {time_str}")
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")

def seconds_to_time(seconds: int, format_type: str) -> str:
    if format_type == "MM:SS":
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def add_times(time1: str, time2: str) -> str:
    """
    Adds two time strings together.
    
    Both times must be in the same format: either "MM:SS" (minutes:seconds) or 
    "HH:MM:SS" (hours:minutes:seconds). The result will be returned in the same 
    format as the first time argument.
    
    Examples:
        add_times("05:30", "02:15") -> "07:45"
        add_times("01:30:45", "00:45:20") -> "02:16:05"
    
    Args:
        time1: First time string in format "MM:SS" or "HH:MM:SS"
        time2: Second time string in format "MM:SS" or "HH:MM:SS"
        
    Returns:
        String with the sum of both times in the same format as time1
        
    Raises:
        ValueError: If either time string is not in a valid format
    """
    if not validate_time_format(time1):
        raise ValueError(f"Invalid time format for time1: {time1}. Expected 'MM:SS' or 'HH:MM:SS'")
    if not validate_time_format(time2):
        raise ValueError(f"Invalid time format for time2: {time2}. Expected 'MM:SS' or 'HH:MM:SS'")
    
    time1_format = "HH:MM:SS" if len(time1.split(":")) == 3 else "MM:SS"
    time2_format = "HH:MM:SS" if len(time2.split(":")) == 3 else "MM:SS"
    
    if time1_format != time2_format:
        raise ValueError(f"Time formats must match. time1 is {time1_format}, time2 is {time2_format}")
    
    total_seconds = time_to_seconds(time1) + time_to_seconds(time2)
    return seconds_to_time(total_seconds, time1_format)

def shift_subtask_times(subtasks: Subtasks, gap: str) -> Subtasks:
    if len(subtasks.subtasks) == 0:
        return subtasks
    
    last_end_time = subtasks.subtasks[-1].end_time
    time_format = "HH:MM:SS" if len(last_end_time.split(":")) == 3 else "MM:SS"
    gap_seconds = time_to_seconds(gap)
    
    for i in range(len(subtasks.subtasks)):
        if i == 0:
            subtasks.subtasks[i].start_time = "00:00"
        else:
            subtasks.subtasks[i].start_time = subtasks.subtasks[i-1].end_time
        
        if i == len(subtasks.subtasks) - 1:
            subtasks.subtasks[i].end_time = last_end_time
        else:
            current_end_seconds = time_to_seconds(subtasks.subtasks[i].end_time)
            new_end_seconds = current_end_seconds + gap_seconds
            subtasks.subtasks[i].end_time = seconds_to_time(new_end_seconds, time_format)
    
    return subtasks


def distribute_gaps_between_annotations(annotations: list) -> list:
    """
    Distribuye el espacio en blanco entre subtareas consecutivas ajustando los frames.
    
    Para cada par de subtareas consecutivas:
    - subtask 1: [a, b]
    - subtask 2: [c, d]
    - gap = c - b
    - r = gap / 2
    - nueva subtask 1: [a, b + r]
    - nueva subtask 2: [c - r, d]
    
    Args:
        annotations: Lista de diccionarios con las anotaciones, cada una debe tener
                    'start_frame' y 'end_frame'
    
    Returns:
        Lista de anotaciones con frames ajustados
    """
    if len(annotations) <= 1:
        return annotations
    
    # Crear copia para no modificar el original
    adjusted_annotations = [ann.copy() for ann in annotations]
    
    for i in range(len(adjusted_annotations) - 1):
        current = adjusted_annotations[i]
        next_task = adjusted_annotations[i + 1]
        
        b = current['end_frame']
        c = next_task['start_frame']
        
        # Calcular el gap entre tareas
        gap = c - b
        
        # Si hay un gap, distribuirlo
        if gap > 0:
            r = gap / 2
            
            # Ajustar end_frame de la tarea actual
            adjusted_annotations[i]['end_frame'] = int(b + r)
            
            # Ajustar start_frame de la siguiente tarea
            adjusted_annotations[i + 1]['start_frame'] = int(c - r)
    
    return adjusted_annotations