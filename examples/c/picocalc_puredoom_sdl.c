/*
 * PicoCalc PureDOOM SDL frontend.
 *
 * This keeps the first Luckfox Lyra build small: SDL2/DirectFB handles
 * framebuffer/input, PureDOOM handles the game core, and audio is intentionally
 * disabled for the first install.
 */

#define SDL_MAIN_HANDLED
#define DOOM_EXAMPLE_USE_SINGLE_HEADER
#define DOOM_IMPLEMENTATION
#define DOOM_IMPLEMENT_PRINT
#define DOOM_IMPLEMENT_MALLOC
#define DOOM_IMPLEMENT_FILE_IO
#define DOOM_IMPLEMENT_GETTIME
#define DOOM_IMPLEMENT_EXIT
#define DOOM_IMPLEMENT_GETENV

#include <SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "PureDOOM.h"

#define DOOM_WIDTH 320
#define DOOM_HEIGHT 200
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 320
#define VIEW_HEIGHT 240

static doom_key_t sdl_scancode_to_doom_key(SDL_Scancode scancode)
{
    switch (scancode)
    {
        case SDL_SCANCODE_TAB: return DOOM_KEY_TAB;
        case SDL_SCANCODE_RETURN: return DOOM_KEY_CTRL;
        case SDL_SCANCODE_ESCAPE: return DOOM_KEY_ESCAPE;
        case SDL_SCANCODE_SPACE: return DOOM_KEY_SPACE;
        case SDL_SCANCODE_APOSTROPHE: return DOOM_KEY_APOSTROPHE;
        case SDL_SCANCODE_KP_MULTIPLY: return DOOM_KEY_MULTIPLY;
        case SDL_SCANCODE_COMMA: return DOOM_KEY_COMMA;
        case SDL_SCANCODE_MINUS: return DOOM_KEY_MINUS;
        case SDL_SCANCODE_PERIOD: return DOOM_KEY_PERIOD;
        case SDL_SCANCODE_SLASH: return DOOM_KEY_SLASH;
        case SDL_SCANCODE_0: return DOOM_KEY_0;
        case SDL_SCANCODE_1: return DOOM_KEY_1;
        case SDL_SCANCODE_2: return DOOM_KEY_2;
        case SDL_SCANCODE_3: return DOOM_KEY_3;
        case SDL_SCANCODE_4: return DOOM_KEY_4;
        case SDL_SCANCODE_5: return DOOM_KEY_5;
        case SDL_SCANCODE_6: return DOOM_KEY_6;
        case SDL_SCANCODE_7: return DOOM_KEY_7;
        case SDL_SCANCODE_8: return DOOM_KEY_8;
        case SDL_SCANCODE_9: return DOOM_KEY_9;
        case SDL_SCANCODE_SEMICOLON: return DOOM_KEY_SEMICOLON;
        case SDL_SCANCODE_EQUALS: return DOOM_KEY_EQUALS;
        case SDL_SCANCODE_LEFTBRACKET: return DOOM_KEY_LEFT_BRACKET;
        case SDL_SCANCODE_RIGHTBRACKET: return DOOM_KEY_RIGHT_BRACKET;
        case SDL_SCANCODE_A: return DOOM_KEY_A;
        case SDL_SCANCODE_B: return DOOM_KEY_B;
        case SDL_SCANCODE_C: return DOOM_KEY_C;
        case SDL_SCANCODE_D: return DOOM_KEY_D;
        case SDL_SCANCODE_E: return DOOM_KEY_E;
        case SDL_SCANCODE_F: return DOOM_KEY_F;
        case SDL_SCANCODE_G: return DOOM_KEY_G;
        case SDL_SCANCODE_H: return DOOM_KEY_H;
        case SDL_SCANCODE_I: return DOOM_KEY_I;
        case SDL_SCANCODE_J: return DOOM_KEY_J;
        case SDL_SCANCODE_K: return DOOM_KEY_K;
        case SDL_SCANCODE_L: return DOOM_KEY_L;
        case SDL_SCANCODE_M: return DOOM_KEY_M;
        case SDL_SCANCODE_N: return DOOM_KEY_N;
        case SDL_SCANCODE_O: return DOOM_KEY_O;
        case SDL_SCANCODE_P: return DOOM_KEY_P;
        case SDL_SCANCODE_Q: return DOOM_KEY_Q;
        case SDL_SCANCODE_R: return DOOM_KEY_R;
        case SDL_SCANCODE_S: return DOOM_KEY_DOWN_ARROW;
        case SDL_SCANCODE_T: return DOOM_KEY_T;
        case SDL_SCANCODE_U: return DOOM_KEY_U;
        case SDL_SCANCODE_V: return DOOM_KEY_V;
        case SDL_SCANCODE_W: return DOOM_KEY_UP_ARROW;
        case SDL_SCANCODE_X: return DOOM_KEY_X;
        case SDL_SCANCODE_Y: return DOOM_KEY_Y;
        case SDL_SCANCODE_Z: return DOOM_KEY_Z;
        case SDL_SCANCODE_BACKSPACE: return DOOM_KEY_BACKSPACE;
        case SDL_SCANCODE_LCTRL:
        case SDL_SCANCODE_RCTRL: return DOOM_KEY_CTRL;
        case SDL_SCANCODE_LEFT: return DOOM_KEY_LEFT_ARROW;
        case SDL_SCANCODE_UP: return DOOM_KEY_UP_ARROW;
        case SDL_SCANCODE_RIGHT: return DOOM_KEY_RIGHT_ARROW;
        case SDL_SCANCODE_DOWN: return DOOM_KEY_DOWN_ARROW;
        case SDL_SCANCODE_LSHIFT:
        case SDL_SCANCODE_RSHIFT: return DOOM_KEY_SHIFT;
        case SDL_SCANCODE_LALT:
        case SDL_SCANCODE_RALT: return DOOM_KEY_ALT;
        case SDL_SCANCODE_F1: return DOOM_KEY_F1;
        case SDL_SCANCODE_F2: return DOOM_KEY_F2;
        case SDL_SCANCODE_F3: return DOOM_KEY_F3;
        case SDL_SCANCODE_F4: return DOOM_KEY_F4;
        case SDL_SCANCODE_F5: return DOOM_KEY_F5;
        case SDL_SCANCODE_F6: return DOOM_KEY_F6;
        case SDL_SCANCODE_F7: return DOOM_KEY_F7;
        case SDL_SCANCODE_F8: return DOOM_KEY_F8;
        case SDL_SCANCODE_F9: return DOOM_KEY_F9;
        case SDL_SCANCODE_F10: return DOOM_KEY_F10;
        case SDL_SCANCODE_F11: return DOOM_KEY_F11;
        case SDL_SCANCODE_F12: return DOOM_KEY_F12;
        case SDL_SCANCODE_PAUSE: return DOOM_KEY_PAUSE;
        default: return DOOM_KEY_UNKNOWN;
    }
}

static int should_exit_hotkey(const SDL_KeyboardEvent* event)
{
    return event->keysym.scancode == SDL_SCANCODE_F5 && (event->keysym.mod & KMOD_CTRL);
}

int main(int argc, char** argv)
{
    setenv("SDL_VIDEODRIVER", "directfb", 0);
    setenv("SDL_AUDIODRIVER", "dummy", 0);
    setenv("DOOMWADDIR", "/usr/share/puredoom", 0);

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER) != 0)
    {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }

    SDL_Window* window = SDL_CreateWindow(
        "PureDOOM PicoCalc",
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SDL_WINDOW_SHOWN);
    if (!window)
    {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_SOFTWARE);
    if (!renderer)
    {
        fprintf(stderr, "SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    SDL_Texture* texture = SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_ABGR8888,
        SDL_TEXTUREACCESS_STREAMING,
        DOOM_WIDTH,
        DOOM_HEIGHT);
    if (!texture)
    {
        fprintf(stderr, "SDL_CreateTexture failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    doom_set_default_int("key_up", DOOM_KEY_UP_ARROW);
    doom_set_default_int("key_down", DOOM_KEY_DOWN_ARROW);
    doom_set_default_int("key_strafeleft", DOOM_KEY_A);
    doom_set_default_int("key_straferight", DOOM_KEY_D);
    doom_set_default_int("key_use", DOOM_KEY_E);
    doom_set_default_int("mouse_move", 0);
    doom_set_resolution(DOOM_WIDTH, DOOM_HEIGHT);

    doom_init(argc, argv, DOOM_FLAG_MENU_DARKEN_BG);

    int done = 0;
    while (!done)
    {
        SDL_Event event;
        while (SDL_PollEvent(&event))
        {
            switch (event.type)
            {
                case SDL_QUIT:
                    done = 1;
                    break;
                case SDL_KEYDOWN:
                    if (should_exit_hotkey(&event.key))
                    {
                        done = 1;
                        break;
                    }
                    if (!event.key.repeat)
                        doom_key_down(sdl_scancode_to_doom_key(event.key.keysym.scancode));
                    break;
                case SDL_KEYUP:
                    if (!event.key.repeat)
                        doom_key_up(sdl_scancode_to_doom_key(event.key.keysym.scancode));
                    break;
            }
        }

        doom_update();

        const unsigned char* src = doom_get_framebuffer(4);
        void* dst = NULL;
        int dst_pitch = 0;
        if (SDL_LockTexture(texture, NULL, &dst, &dst_pitch) == 0)
        {
            const int src_pitch = DOOM_WIDTH * 4;
            unsigned char* dst8 = (unsigned char*)dst;
            for (int y = 0; y < DOOM_HEIGHT; ++y)
                memcpy(dst8 + (y * dst_pitch), src + (y * src_pitch), src_pitch);
            SDL_UnlockTexture(texture);
        }

        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);
        SDL_Rect dst_rect = {0, (SCREEN_HEIGHT - VIEW_HEIGHT) / 2, SCREEN_WIDTH, VIEW_HEIGHT};
        SDL_RenderCopy(renderer, texture, NULL, &dst_rect);
        SDL_RenderPresent(renderer);
    }

    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
