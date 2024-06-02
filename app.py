import flet as ft
import cv2
import numpy as np
import base64
import threading
import time

# Конвертирует в бейс
def to_base64(image):
    _, buffer = cv2.imencode('.png', image)
    base64_image = base64.b64encode(buffer).decode("utf-8")
    return base64_image

# функция для вызова эффектов
def apply_effects(frame, brightness=1.0, contrast=1.0, saturation=1.0, blur=0):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[...,1] = np.clip(hsv[...,1] * saturation, 0, 255)
    frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness*50)
    if blur > 0:
        frame = cv2.blur(frame, (blur, blur), 0)
    return frame

def main(page):
    
    # Функция для кнопки, которая возвращает эффекты в исходное состояние
    def reset_settings(e):
        brightness_slider.value = 0
        contrast_slider.value = 1.0
        saturation_slider.value = 1.0
        blur_slider.value = 0
        video_seek_slider.value = 0
        page.update()
    # Функция паузы
    def toggle_pause():
        nonlocal paused
        paused = not paused
        pause_button.icon = ft.icons.PLAY_ARROW if paused else ft.icons.PAUSE
        page.update()
    # Таймлайн
    def seek_video(value):
        nonlocal current_frame
        if cap and total_frames > 0:
            current_frame = int(value * total_frames / 100)
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
    # Синхронизация видео и модуля флет
    def update_frame():
        nonlocal current_frame, total_frames
        while cap.isOpened():
            if paused:
                time.sleep(0.1)
                continue
            ret, frame = cap.read()
            if not ret:
                break
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            frame = apply_effects(
                frame,
                brightness=brightness_slider.value / 100,
                contrast=contrast_slider.value,
                saturation=saturation_slider.value,
                blur=int(blur_slider.value)
            )
            base64_image = to_base64(frame)
            video_src.src_base64 = base64_image
            video_seek_slider.value = (current_frame / total_frames) * 100
            page.update()
            time.sleep(1/60)
        cap.release()

    # выбор видео файла для обработки 
    def on_file_selected(e):
        nonlocal video_path, cap, total_frames
        if e.files:
            video_path = e.files[0].path
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            threading.Thread(target=update_frame, daemon=True).start()
    # открываеться панель
    def on_click(e):
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.VIDEO)

    # выход из приложения 
    def exit_app(e):
        page.window_close()

    # Перезагрузка страницы
    def reload_page(e):
        page.controls.clear()
        page.add(section)
        page.update()

    # включение\выключение панели с файлами 
    def toggle_file_panel(e):
        file_panel.visible = not file_panel.visible
        file_panel.update()

    # включение\выключение панели с АИ
    def toggle_AI_panel(e):
        AI_tab.visible = not AI_tab.visible
        AI_tab.update()

    # включение\выключение панели с информацией
    def toggle_info_panel(e):
        info_panel.visible = not info_panel.visible
        info_panel.update()

    # включение\выключение панели с эффектами
    def toggle_effect_panel(e):
        effects_tab.visible = not effects_tab.visible
        effects_tab.update()
    
    init_image = np.zeros((720, 1280, 3), dtype=np.uint8) + 128 # создание серого экрана 1280 на 720
    init_base64_image = to_base64(init_image)

    video_src = ft.Image(src_base64=init_base64_image, width=1280, height=720)
    brightness_slider = ft.Slider(min=-100, max=100, value=0, label="Brightness", 
                                  active_color=ft.colors.GREY, inactive_color=ft.colors.GREY, thumb_color=ft.colors.GREY_400)
    contrast_slider = ft.Slider(min=0.5, max=3.0, value=1.0, label="Contrast", 
                                active_color=ft.colors.GREY, inactive_color=ft.colors.GREY, thumb_color=ft.colors.GREY_400)
    saturation_slider = ft.Slider(min=0.5, max=3.0, value=1.0, label="Saturation",
                                   active_color=ft.colors.GREY, inactive_color=ft.colors.GREY, thumb_color=ft.colors.GREY_400)
    blur_slider = ft.Slider(min=0, max=50, value=0, label="Blur", active_color=ft.colors.GREY, 
                            inactive_color=ft.colors.GREY, thumb_color=ft.colors.GREY_400)
    video_seek_slider = ft.Slider(min=0, max=100, value=0, label="Seek", width=1280, height=20, on_change=lambda e: seek_video(int(e.control.value)), 
        active_color=ft.colors.GREY, inactive_color=ft.colors.GREY, thumb_color=ft.colors.GREY_400)
    pause_button = ft.IconButton(icon=ft.icons.PAUSE, on_click=lambda e: toggle_pause(), bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE)

    video_path = None
    cap = None
    paused = False
    current_frame = 0
    total_frames = 0
        
    file_picker = ft.FilePicker(on_result=on_file_selected)
    page.overlay.append(file_picker)

    # Кнопки действий
    select_button = ft.ElevatedButton("Select Video File", on_click=on_click, bgcolor=ft.colors.GREY_700, color=ft.colors.WHITE)
    reset_button = ft.IconButton(icon=ft.icons.REFRESH, on_click=reset_settings, bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE)
    effect_button = ft.Container(margin=5, content=ft.CupertinoButton(" Effects ", on_click=toggle_effect_panel, bgcolor=ft.colors.GREY_700, color=ft.colors.WHITE,))
    AI_button = ft.Container(margin=5, content = ft.CupertinoButton("     AI     ", on_click=toggle_AI_panel, bgcolor=ft.colors.GREY_700, color=ft.colors.WHITE,))
    file_icon = ft.Container(margin=10, content = ft.IconButton(icon=ft.icons.FOLDER_OPEN,on_click=toggle_file_panel, bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE))
    info_icon = ft.Container(margin=10, content = ft.IconButton(icon=ft.icons.INFO_OUTLINE_ROUNDED,on_click=toggle_info_panel, bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE))
    Track_face_button = ft.Container(margin=10, content = ft.IconButton(icon=ft.icons.FACE_ROUNDED, bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE))
    Track_the_number = ft.Container(margin=10, content = ft.IconButton(icon=ft.icons.NUMBERS, bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE))
    Track_the_car = ft.Container(margin=10, content = ft.IconButton(icon=ft.icons.CAR_CRASH, bgcolor=ft.colors.GREY_700, icon_color=ft.colors.WHITE))

    # вкладка эффектов
    effects_tab = ft.Container(
        visible=False,
        width=190,
        padding=15,
        bgcolor=ft.colors.GREY_700,
        border_radius=10,
        content = ft.Column([
            ft.Text("Brightness", size=12, weight="bold", color=ft.colors.WHITE),
            brightness_slider,
            ft.Text("Contrast", size=12, weight="bold", color=ft.colors.WHITE),
            contrast_slider,
            ft.Text("Saturation", size=12, weight="bold", color=ft.colors.WHITE),
            saturation_slider,
            ft.Text("Blur", size=12, weight="bold", color=ft.colors.WHITE),
            blur_slider,
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
        )
    )

    # Вкладка АИ
    AI_tab = ft.Container(
        visible=False,
        width=190,
        padding=15,
        bgcolor=ft.colors.GREY_700,
        border_radius=10,
        content = ft.Column([
            ft.Text("Track face", size=12, weight="bold", color=ft.colors.WHITE),
            Track_face_button,
            ft.Text("Track the number", size=12, weight="bold", color=ft.colors.WHITE),
            Track_the_number,
            ft.Text("Track the car", size=12, weight="bold", color=ft.colors.WHITE),
            Track_the_car
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True    
        )
    )

    # Эффект панель
    effect_panel = ft.Container(
        padding=10,
        width=210,
        bgcolor=ft.colors.GREY_800,
        content=ft.Column(
            [
                ft.Text("Action panel", size=20, weight="bold", color=ft.colors.WHITE),
                effect_button,
                effects_tab,
                AI_button,
                AI_tab
        ], 
        spacing=0,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

    # будет позже
    Soon_panel = ft.Container(
        width=210,
        bgcolor=ft.colors.GREY_800,
        )
    
    # Верхняя паенль с перезагрузкой эффектов и импортом файла 
    top_panel = ft.Container(
        height=70,
        bgcolor=ft.colors.GREY_800,
        padding=0,
        content = ft.Row([select_button, reset_button], alignment=ft.MainAxisAlignment.CENTER)
    )

    # вкладка с файлами 
    file_panel = ft.Container(
        visible=False,
        content=ft.Column(
            [
                ft.CupertinoButton(text="New file..", on_click=reload_page,color=ft.colors.WHITE),
                ft.CupertinoButton(text="Save", color=ft.colors.WHITE),
                ft.CupertinoButton(text="Save as..", color=ft.colors.WHITE),
                ft.CupertinoButton(text="Exit", on_click=exit_app, color=ft.colors.WHITE),
            ],
            spacing=-10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # вкладка информация
    info_panel = ft.Container(
        visible=False,
        content=ft.Column(
            [
                ft.CupertinoButton(text="Welcome", color=ft.colors.WHITE),
                ft.CupertinoButton(text="Edit", color=ft.colors.WHITE),
                ft.CupertinoButton(text="Report", color=ft.colors.WHITE),
                ft.CupertinoButton(text="About", color=ft.colors.WHITE),
            ],
            spacing=-10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # левая панель 
    left_panel = ft.Container(
        width=150,
        bgcolor=ft.colors.GREY_800,
        content=ft.Column(
            [
                file_icon,
                file_panel,
                info_icon,
                info_panel
        ], 
        spacing=-10,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

    # экранная паенль
    screen_panel = ft.Container(
        bgcolor=ft.colors.GREY_800,
        padding=10,
        content=ft.Column([
            video_src,
            pause_button,
            video_seek_slider
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True 
        )
    )

    # конструктор для создания 
    section = ft.Container(
        content=ft.Column(
            [
            top_panel,
            ft.Row([left_panel, screen_panel, effect_panel, Soon_panel],
                expand=True
                )
            ], 
        alignment=ft.MainAxisAlignment.START), 
        expand=True
    )
    
    # заданные параметры для страницы 
    page.bgcolor = ft.colors.GREY_900
    page.add(section)

ft.app(target=main)
