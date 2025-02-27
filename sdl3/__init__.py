__version__ = "0.9.3"

from pathlib import Path
import sys, os, ctypes, ctypes.util, platform, keyword, inspect, types, \
    asyncio, zipfile, typing, array, packaging.version, json, re

class STUBS:
    def __init__(self, name):
        self.__name__ = name
    def __getattr__(self, name):
        def any(*argv, **kw):
            print(f"{self.__name__}.{name} STUB {argv} {kw}", file=sys.stderr)
        return any

atexit = STUBS("atexit")
stubs = STUBS("sdl3")
currentBinary = None


def SDL_FIND_BINARIES(libraries: typing.List[str]) -> typing.List[str]:
    return (Path(__file__).parent / "libsdl.so").as_posix()

try:
    # pre inited by main.py
    SDL_DLL
except NameError:
    import platform

    # sane default
    WIDTH=1024
    HEIGHT=600

    platform.window.canvas.width = WIDTH
    platform.window.canvas.height = HEIGHT
    platform.window.canvas.style.width = f"{WIDTH}px"
    platform.window.canvas.style.height = f"{HEIGHT}px"

    import builtins
    sdl3so = SDL_FIND_BINARIES("SDL3")

    if os.path.isfile(sdl3so):
        print("dynamic SDL3")
    else:
        print("static SDL3")
        sdl3so = None

    builtins.SDL_DLL = ctypes.CDLL(sdl3so)
    os.environ['SDL_VIDEO_DRIVER'] = 'emscripten'
    os.environ['SDL_RENDER_DRIVER'] = os.environ.get('SDL_RENDER_DRIVER', 'software')
    software = (os.environ['SDL_RENDER_DRIVER'] == 'software')
    if software:
        print(" -- software rendering --")


SDL_BINARY, SDL_IMAGE_BINARY, SDL_MIXER_BINARY, SDL_TTF_BINARY, SDL_RTF_BINARY, SDL_NET_BINARY = \
    "SDL3", "SDL3_image", "SDL3_mixer", "SDL3_ttf", "SDL3_rtf", "SDL3_net"

SDL_BINARY_VAR_MAP: typing.Dict[str, str] = {}

for i in locals().copy():
    if i.startswith("SDL_") and i.endswith("_BINARY"):
        SDL_BINARY_VAR_MAP[i] = locals()[i]

SDL_BINARY_VAR_MAP_INV: typing.Dict[str, str] = {value: key for key, value in SDL_BINARY_VAR_MAP.items()}
SDL_REPOSITORIES: typing.List[str] = [key.replace("3", "") for key, _ in SDL_BINARY_VAR_MAP_INV.items()]

def SDL_FORMAT_ARCH(arch: str) -> str:
    return "wasm32"

SDL_SYSTEM, SDL_ARCH = platform.system(), SDL_FORMAT_ARCH(platform.machine())
SDL_BINARY_PATTERNS: typing.Dict[str, typing.List[str]] = \
    {"Windows": ["{}.dll"], "Darwin": ["lib{}.dylib", "{0}.framework/{0}", "{0}.framework/Versions/A/{0}"], "Linux": ["lib{}.so"]}

def SDL_PLATFORM_SPECIFIC(system: typing.List[str] = None, arch: typing.List[str] = None) -> bool:
    """Check if the current platform is inside the given platforms."""
    if int(os.environ.get("SDL_PLATFORM_AGNOSTIC", "0")) > 0: return True
    return (not system or SDL_SYSTEM in system) and (not arch or SDL_ARCH in arch)

__frozen__: bool = getattr(sys, "frozen", False)
__initialized__: bool = __name__.split(".")[0] in sys.modules if "." in __name__ else False
__module__: types.ModuleType = sys.modules[__name__.split(".")[0] if "." in __name__ else __name__]


def SDL_DOWNLOAD_BINARIES(path: str, system: str = SDL_SYSTEM, arch: str = SDL_ARCH) -> None:
    print("""Download specific SDL3 binaries to the given path.""")

binaryMap = {}
functions = {
    "SDL3":{}
}
functions["SDL3_image"] =    functions["SDL3"]
functions["SDL3_mixer"] =    functions["SDL3"]
functions["SDL3_net"]   =    functions["SDL3"]
functions["SDL3_rtf"]   =    functions["SDL3"]
functions["SDL3_ttf"]   =    functions["SDL3"]

def SDL_ARRAY(*args: typing.List[typing.Any], **kwargs: typing.Dict[str, typing.Any]) -> typing.Tuple[ctypes.Array[typing.Any], int]:
    """Create a ctypes array."""
    return ((kwargs.get("type") or args[0].__class__) * len(args))(*args), len(args)

def SDL_DEREFERENCE(value: typing.Any) -> typing.Any:
    """Dereference a ctypes pointer or object."""
    if isinstance(value, ctypes._Pointer): return value.contents
    elif hasattr(value, "_obj"): return value._obj
    else: return value

def SDL_CACHE_FUNC(func: typing.Callable) -> typing.Callable:
    """Simple function cache decorator."""
    cache = {}

    def __inner__(*args: typing.List[typing.Any], **kwargs: typing.Dict[str, typing.Any]) -> typing.Any:
        _hash = hash((args, tuple(frozenset(sorted(kwargs.items())))))
        if _hash not in cache: cache.update({_hash: func(*args, **kwargs)})
        return cache.get(_hash, None)

    return __inner__

@SDL_CACHE_FUNC
def SDL_GET_BINARY_NAME(binary: typing.Any) -> str:
    """Get the name of an SDL3 binary."""
    return {v: k for k, v in __module__.binaryMap.items()}.get(binary, None)

def SDL_GET_BINARY(name: str) -> typing.Any:
    """Get an SDL3 binary by its name."""
    return __module__.binaryMap.get(name)

def SDL_SET_CURRENT_BINARY(name: str) -> None:
    cur = ( SDL_DLL, name)
    if __module__.currentBinary != cur:
        print(f"""Set the current SDL3 binary by its name {name}.""")
        __module__.currentBinary = cur


def SDL_GET_CURRENT_BINARY() -> typing.Any:
    """Get the current SDL3 binary."""
    return __module__.currentBinary

def SDL_NOT_IMPLEMENTED(name: str) -> typing.Callable:
    return lambda *args, **kwargs: print("\33[31m", f"error: invoked an unimplemented function: '{name}'.", "\33[0m", sep = "", flush = True)

def SDL_FUNC(name: str, retType: typing.Any, *argTypes: typing.List[typing.Any]) -> None:
    """Define an SDL3 function."""

    if (binary := SDL_GET_CURRENT_BINARY())[0] and hasattr(binary[0], name):
        func = getattr(binary[0], name)
        setattr(__module__, name, func)
    else:
        if sys.flags.inspect: # should be sys.flags.interactive here.
            print("\33[35m", f"warning: function '{name}' not found in binary: '{binary[1]}'.", "\33[0m", sep = "", flush = True, file=sys.stderr)
        func = getattr(stubs, name)


    func.restype, func.argtypes, func.binary = retType, argTypes, binary[0]
    __module__.functions[binary[1]][name] = func

    setattr(__module__, name, func)

from sdl3.SDL import *

