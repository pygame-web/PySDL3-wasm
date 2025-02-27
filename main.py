# /// script
# dependencies = [
#   "sdl3",
# ]
# ///

import asyncio
import os
import sys
import ctypes
import colorsys
import time

wasm=sys.platform in ('emscripten','wasi')

if wasm:
    import platform

if 0:
    WIDTH = 1024
    HEIGHT = 600

    if wasm:
        platform.window.canvas.width = WIDTH
        platform.window.canvas.height = HEIGHT
        platform.window.canvas.style.width = f"{WIDTH}px"
        platform.window.canvas.style.height = f"{HEIGHT}px"

        import builtins

        if os.path.isfile('sdl3/libsdl.so'):
            print("dynamic SDL3")
            builtins.SDL_DLL = ctypes.CDLL("sdl3/libsdl.so")
        else:
            print("static SDL3")
            builtins.SDL_DLL = ctypes.CDLL(None)
        os.environ['SDL_VIDEO_DRIVER'] = 'emscripten'
        software = True

    else:
        os.environ['SDL_VIDEO_DRIVER'] = 'x11,wayland'
        software = 'soft' in sys.argv


import sdl3
try:
    software = sdl3.software
except:
    software = False

if 'pyodide' in os.environ.get('HOME',''):
    sdl3.frametime = 0.016
elif wasm:
    sdl3.frametime = 0
else:
    # todo get vsync.
    sdl3.frametime = 0.016



sdl3.TTF_Init()


async def main(argc: ctypes.c_int, argv: sdl3.LP_c_char_p) -> ctypes.c_int:
    try:
        print(
            f"total lines of code: {sum([len(open(f'sdl3/{i}', 'r').readlines()) for i in os.listdir('sdl3') if i.endswith('.py')])}."
        )
    except:
        pass
    print(f"loaded {sum(len(v) for k, v in sdl3.functions.items())} functions.")


    if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS):  # | sdl3.SDL_INIT_AUDIO):
        print(f"failed to initialize library: {sdl3.SDL_GetError().decode().lower()}.")
        return -1

    window = sdl3.SDL_CreateWindow("Aermoss".encode(), 1024, 600, sdl3.SDL_WINDOW_TRANSPARENT, sdl3.SDL_WINDOW_RESIZABLE)




    if software:
        display = sdl3.SDL_GetWindowSurface(window);
        renderer = sdl3.SDL_CreateSoftwareRenderer(display);
    else:
        display = None # surface lives in GPU/renderer

        renderDrivers = [sdl3.SDL_GetRenderDriver(i).decode() for i in range(sdl3.SDL_GetNumRenderDrivers())]
        tryGetDriver, tryUseVulkan = lambda order, drivers: next((i for i in order if i in drivers), None), False
        renderDriver = tryGetDriver((["vulkan"] if tryUseVulkan else []) + ["opengl", "software"], renderDrivers)
        print(f"available render drivers: {', '.join(renderDrivers)} (current: {renderDriver}).")

        if not (renderer := sdl3.SDL_CreateRenderer(window, renderDriver.encode())):
            print(f"failed to create renderer: {sdl3.SDL_GetError().decode().lower()}.")
            return -1

    audioDrivers = [sdl3.SDL_GetAudioDriver(i).decode() for i in range(sdl3.SDL_GetNumAudioDrivers())]
    currentAudioDevice = None
    if audioDrivers:
        if sdl3.SDL_GetCurrentAudioDriver():
            print(f"available audio drivers: {', '.join(audioDrivers)} (current: {sdl3.SDL_GetCurrentAudioDriver().decode().lower()}).")

            if currentAudioDevice := sdl3.SDL_OpenAudioDevice(sdl3.SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, None):
                sdl3.Mix_Init(sdl3.MIX_INIT_WAVPACK)
                sdl3.Mix_OpenAudio(currentAudioDevice, ctypes.byref(audioSpec := sdl3.SDL_AudioSpec()))
                print(f"current audio device: {sdl3.SDL_GetAudioDeviceName(currentAudioDevice).decode().lower()}.")
                chunks = [sdl3.Mix_LoadWAV(f"res/voice/{i}".encode()) for i in os.listdir("res/voice")]
                currentIndex, channel = 0, 0

            else:
                print(
                    f"failed to open audio device: {sdl3.SDL_GetAudioDeviceName(sdl3.SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK).decode().lower()}, error: {sdl3.SDL_GetError().decode().lower()}."
                )

    if not currentAudioDevice:
        print(" -- no audio --")

    tex_surf = sdl3.IMG_Load("res/example.png".encode())

    if wasm:
        await asyncio.sleep(0)
        platform.window.window_resize()

    tex = sdl3.SDL_CreateTextureFromSurface(renderer, tex_surf)

    rect = sdl3.SDL_Rect()
    sdl3.SDL_GetSurfaceClipRect(tex_surf, ctypes.byref(rect))

    frect = sdl3.SDL_FRect()
    sdl3.SDL_RectToFRect(ctypes.byref(rect), ctypes.byref(frect))
    running, hue, lastTime, scale = True, 0.0, time.time(), 0.75

    font = sdl3.TTF_OpenFont("res/example.ttf".encode(), 32.0)

    frames, frameCooldown = 0.0, 1.0
    textTexture, textFRect = None, sdl3.SDL_FRect()
    sinceLastFrame = frameCooldown
    event = sdl3.SDL_Event()
    if error := sdl3.SDL_GetError():
        print(f"118:error: {error.decode().lower()}.")

    lwidth, lheight = ctypes.c_int(), ctypes.c_int()
    sdl3.SDL_GetWindowSize(window, lwidth, lheight)

    width, height = ctypes.c_int(), ctypes.c_int()
    sdl3.SDL_GetWindowSizeInPixels(window, width, height)


    print(f"""

Pixels:
    Width: {width} Heidth: {height}

Logical:
    Width: {lwidth} Heidth: {lheight}

Surface: {tex_surf}
Texture: {tex}

window:  {window}
display: {display}
render:  {renderer}

 rect: {rect} {rect.w}x{rect.h}+{rect.x},{rect.y}
frect: {frect} {frect.w}x{frect.h}+{frect.x},{frect.y}


""")

    while running:
        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            match event.type:
                case sdl3.SDL_EVENT_KEY_DOWN:
                    if event.key.key in [sdl3.SDLK_ESCAPE]:
                        running = False
                case sdl3.SDL_EVENT_QUIT:
                    running = False


        frect.w, frect.h = frect.w * width.value / frect.w * scale, frect.h * width.value / frect.w * scale
        frect.x, frect.y = width.value / 2 - frect.w / 2, height.value / 2 - frect.h / 2

        if currentAudioDevice and not sdl3.Mix_Playing(channel):
            channel = sdl3.Mix_PlayChannel(-1, chunks[currentIndex], 1)
            if (currentIndex := currentIndex + 1) >= len(chunks):
                currentIndex = 0

        lastTime, deltaTime = time.time(), time.time() - lastTime
        hue, frames = (hue + 0.5 * deltaTime) % 1.0, frames + 1.0

        sdl3.SDL_SetRenderDrawColorFloat(renderer, *colorsys.hsv_to_rgb(hue, 1.0, 0.1), 1.0)
        sdl3.SDL_RenderClear(renderer)
        sdl3.SDL_RenderTexture(renderer, tex, None, ctypes.byref(frect))

        sinceLastFrame += deltaTime

        if sinceLastFrame >= frameCooldown:
            framesPerSecond = int(frames / sinceLastFrame)
            sinceLastFrame, frames = 0.0, 0.0

            if textTexture is not None:
                sdl3.SDL_DestroySurface(textSurface)
                sdl3.SDL_DestroyTexture(textTexture)

            textSurface = sdl3.TTF_RenderText_Blended(
                font, f"FPS: {framesPerSecond}".encode(), 0, sdl3.SDL_Color(255, 255, 255, 255)
            )
            textTexture = sdl3.SDL_CreateTextureFromSurface(renderer, textSurface)

            textRect = sdl3.SDL_Rect()
            sdl3.SDL_GetSurfaceClipRect(textSurface, ctypes.byref(textRect))
            sdl3.SDL_RectToFRect(ctypes.byref(textRect), ctypes.byref(textFRect))

        if error := sdl3.SDL_GetError():
            print(f"214:error: {error.decode().lower()}.")
            return -1

        if textTexture is not None:
            sdl3.SDL_RenderTexture(renderer, textTexture, None, ctypes.byref(textFRect))

        if error := sdl3.SDL_GetError():
            print(f"220:error: {error.decode().lower()}.")
            return -1

        if software:
            sdl3.SDL_RenderPresent(renderer)
            sdl3.SDL_UpdateWindowSurface(window)

        else:
            sdl3.SDL_RenderPresent(renderer)

        await asyncio.sleep(sdl3.frametime)


        if error := sdl3.SDL_GetError():
            print(f"232:error: {error.decode().lower()}.")
            return -1


    if textTexture is not None:
        sdl3.SDL_DestroySurface(textSurface)
        sdl3.SDL_DestroyTexture(textTexture)

    if currentAudioDevice:
        for i in chunks:
            sdl3.Mix_FreeChunk(i)

        sdl3.Mix_CloseAudio()
        sdl3.Mix_Quit()

    sdl3.TTF_CloseFont(font)
    sdl3.TTF_Quit()

    if display:
        sdl3.SDL_DestroySurface(display)

    sdl3.SDL_DestroySurface(tex_surf)
    sdl3.SDL_DestroyTexture(tex)


    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()
    print('bye')
    return 0


asyncio.run(main(0, []))


