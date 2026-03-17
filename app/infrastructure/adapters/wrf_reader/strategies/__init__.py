"""
wrf_reader/strategies/__init__.py
 
Importing this package registers all built-in virtual-variable strategies.
To add a new one, create a module here and import it below — nothing else changes.
"""
 
def register_all_strategies() -> None:
    """Trigger registration of all built-in variable strategies.
 
    Importing the modules above fires the @register_strategy decorators.
    This function intentionally does nothing — calling it makes the intent
    explicit at the call site instead of relying on a silent side-effect import.
    """
    from . import precipitation
    from . import wind_speed
    from . import wind_direction
    from . import temperature
    from . import pressure
    