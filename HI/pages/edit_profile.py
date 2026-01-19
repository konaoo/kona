"""
编辑个人信息页面
"""
import flet as ft
import base64
from typing import Callable

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from components import page_header, spacer

def build_edit_profile_page(
    state: AppState,
    on_back: Callable
) -> ft.Container:
    
    # 状态
    nickname = state.page.client_storage.get("nickname") or "咔咔用户"
    avatar_base64 = state.page.client_storage.get("avatar_base64")
    
    nickname_field = ft.TextField(
        label="昵称",
        value=nickname,
        border_color=Theme.ACCENT,
        bgcolor=Theme.BG_CARD,
    )
    
    avatar_image = ft.Image(
        src_base64=avatar_base64 if avatar_base64 else None,
        src="/icon.png" if not avatar_base64 else None,
        width=100,
        height=100,
        fit="cover", # 兼容旧版
        border_radius=50,
        error_content=ft.Icon(ft.Icons.PERSON, size=60),
    )
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            # 读取文件并转为 base64
            try:
                with open(file_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    avatar_image.src_base64 = encoded
                    avatar_image.src = "" # 清除默认 src
                    avatar_image.update()
            except Exception as ex:
                print(f"Failed to load image: {ex}")

    file_picker = ft.FilePicker(on_result=on_file_picked)
    state.page.overlay.append(file_picker)
    
    def save_profile(e):
        new_name = nickname_field.value.strip()
        if new_name:
            state.page.client_storage.set("nickname", new_name)
        
        if avatar_image.src_base64:
            state.page.client_storage.set("avatar_base64", avatar_image.src_base64)
            
        on_back(None)
    
    return ft.Container(
        content=ft.Column([
            page_header("编辑资料", on_back=on_back),
            
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=avatar_image,
                        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE),
                        padding=10,
                        border=ft.border.all(2, Theme.ACCENT),
                        border_radius=60,
                    ),
                    ft.Text("点击更换头像", size=12, color=Theme.TEXT_SECONDARY),
                    spacer(Spacing.LG),
                    nickname_field,
                    spacer(Spacing.XL),
                    ft.ElevatedButton(
                        "保存",
                        on_click=save_profile,
                        bgcolor=Theme.ACCENT,
                        color=Theme.TEXT_PRIMARY,
                        height=50,
                        width=200,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                        )
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=Spacing.XL,
                alignment=ft.Alignment(0, 0)
            )
        ]),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )
