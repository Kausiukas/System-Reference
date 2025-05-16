import cProfile
import pstats
import io
import functools
import time
from contextlib import contextmanager
from datetime import datetime

try:
    from line_profiler import LineProfiler
    LINE_PROFILER_AVAILABLE = True
except ImportError:
    LINE_PROFILER_AVAILABLE = False

@contextmanager
def profile_block(name: str = "profile", output_dir: str = "profiles"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    profile_path = os.path.join(output_dir, f"{name}_{timestamp}.prof")
    txt_path = os.path.join(output_dir, f"{name}_{timestamp}.txt")
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        pr.disable()
        pr.dump_stats(profile_path)
        # Also save a human-readable text summary
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(30)  # Top 30 lines
        with open(txt_path, "w") as f:
            f.write(s.getvalue())


def profile_function(func, name: str = None, output_dir: str = "profiles", *args, **kwargs):
    """Profile a function call and save results."""
    if name is None:
        name = func.__name__
    with profile_block(name, output_dir):
        return func(*args, **kwargs)

def profile_function(func=None, *, output_file=None):
    """
    Decorator to profile a function using cProfile. Saves results to output_file if provided.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            pr = cProfile.Profile()
            pr.enable()
            result = f(*args, **kwargs)
            pr.disable()
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats()
            if output_file:
                with open(output_file, 'w') as f_out:
                    f_out.write(s.getvalue())
            else:
                print(s.getvalue())
            return result
        return wrapper
    return decorator if func is None else decorator(func)

@contextmanager
def profile_block(output_file=None):
    """
    Context manager to profile a code block using cProfile.
    """
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    if output_file:
        with open(output_file, 'w') as f_out:
            f_out.write(s.getvalue())
    else:
        print(s.getvalue())


def line_profile_function(func):
    """
    Decorator to profile a function line-by-line (if line_profiler is installed).
    """
    if not LINE_PROFILER_AVAILABLE:
        return func
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        lp = LineProfiler()
        lp.add_function(func)
        lp.enable_by_count()
        result = func(*args, **kwargs)
        lp.disable_by_count()
        lp.print_stats()
        return result
    return wrapper

if __name__ == "__main__":
    import argparse
    import runpy
    parser = argparse.ArgumentParser(description="Profile a Python script or function.")
    parser.add_argument('script', help='Script to profile (e.g., app.py)')
    parser.add_argument('--output', help='Output .prof file', default='profile_output.prof')
    args = parser.parse_args()
    print(f"Profiling {args.script} ...")
    pr = cProfile.Profile()
    pr.enable()
    runpy.run_path(args.script, run_name='__main__')
    pr.disable()
    pr.dump_stats(args.output)
    print(f"Profile saved to {args.output}. Use snakeviz or gprof2dot for visualization.") 