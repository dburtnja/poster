import os
import random
import threading
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox
from playwright.sync_api import sync_playwright

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "groups.txt"


class FBAutoPosterApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("FB AutoPoster for Groups")
        self.geometry("700x750")
        self.minsize(650, 700)

        self.image_paths = []

        self.update_idletasks()
        self.update()

        # Title
        self.lbl_title = ctk.CTkLabel(
            self,
            text="Автоматизація публікацій у Facebook",
            font=("Arial", 20, "bold"),
        )
        self.lbl_title.pack(pady=10)

        # Auth Button
        self.btn_auth = ctk.CTkButton(
            self,
            text="1. Пройти авторизацію / Оновити сесію",
            command=self.run_auth,
            fg_color="#2b5b84",
        )
        self.btn_auth.pack(pady=5)

        # Groups list input
        self.lbl_groups = ctk.CTkLabel(
            self,
            text="Список URL груп (зберігаються у groups.txt, по одній у рядку):",
        )
        self.lbl_groups.pack(anchor="w", padx=20, pady=(10, 0))
        self.txt_groups = ctk.CTkTextbox(self, height=100)
        self.txt_groups.pack(fill="x", padx=20, pady=5)

        self.load_groups_config()
        self.txt_groups.bind(
            "<KeyRelease>", lambda e: self.save_groups_config()
        )

        # Post text input
        self.lbl_text = ctk.CTkLabel(self, text="Текст допису:")
        self.lbl_text.pack(anchor="w", padx=20, pady=(10, 0))
        self.txt_post = ctk.CTkTextbox(self, height=100)
        self.txt_post.pack(fill="x", padx=20, pady=5)

        # Photo selection Frame
        self.frame_photo = ctk.CTkFrame(self)
        self.frame_photo.pack(fill="x", padx=20, pady=10)

        self.btn_photo = ctk.CTkButton(
            self.frame_photo,
            text="Вибрати фото (одне або декілька)",
            command=self.select_photos,
        )
        self.btn_photo.pack(side="left", padx=10, pady=10)

        self.btn_clear_photos = ctk.CTkButton(
            self.frame_photo,
            text="Очистити фото",
            command=self.clear_photos,
            fg_color="#a83232",
            hover_color="#802323",
            width=110,
        )
        self.btn_clear_photos.pack(side="left", padx=5, pady=10)

        self.lbl_photo_path = ctk.CTkLabel(
            self.frame_photo, text="Фото не вибрано", text_color="gray"
        )
        self.lbl_photo_path.pack(side="left", padx=10, pady=10)

        # Start posting button
        self.btn_start = ctk.CTkButton(
            self,
            text="2. Запустити публікацію",
            command=self.start_posting_thread,
            fg_color="#28a745",
            font=("Arial", 14, "bold"),
        )
        self.btn_start.pack(pady=10)

        # Log output
        self.txt_log = ctk.CTkTextbox(self, height=120, state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.update_idletasks()
        self.update()

    def load_groups_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.txt_groups.delete("1.0", "end")
                    self.txt_groups.insert("1.0", content)
            except Exception as e:
                print(f"Помилка зчитування {CONFIG_FILE}: {e}")

    def save_groups_config(self):
        content = self.txt_groups.get("1.0", "end").strip()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Помилка збереження {CONFIG_FILE}: {e}")

    def log(self, message):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"{message}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def select_photos(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")]
        )
        if file_paths:
            for path in file_paths:
                if path not in self.image_paths:
                    self.image_paths.append(path)

            count = len(self.image_paths)
            if count == 1:
                display_text = os.path.basename(self.image_paths[0])
            else:
                display_text = f"Обрано фото: {count} шт."

            self.lbl_photo_path.configure(text=display_text, text_color="white")

    def clear_photos(self):
        self.image_paths = []
        self.lbl_photo_path.configure(
            text="Фото не вибрано", text_color="gray"
        )

    def run_auth(self):
        def auth_task():
            self.log("Запуск браузера для авторизації...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                page.goto("https://www.facebook.com")
                messagebox.showinfo(
                    "Авторизація",
                    "Увійдіть у свій акаунт у браузері, що відкрився, і після цього натисніть ОК у цьому вікні.",
                )
                context.storage_state(path="state.json")
                browser.close()
            self.log("Сесію успішно збережено у state.json!")

        threading.Thread(target=auth_task, daemon=True).start()

    def start_posting_thread(self):
        self.save_groups_config()
        threading.Thread(target=self.run_posting, daemon=True).start()

    def run_posting(self):
        groups = [
            g.strip()
            for g in self.txt_groups.get("1.0", "end").split("\n")
            if g.strip()
        ]
        post_text = self.txt_post.get("1.0", "end").strip()

        if not os.path.exists("state.json"):
            messagebox.showerror("Помилка", "Спочатку пройдіть авторизацію!")
            return

        if not groups:
            messagebox.showerror("Помилка", "Вкажіть хоча б одну групу!")
            return

        self.btn_start.configure(state="disabled")
        self.log(f"Розпочинаємо публікацію у {len(groups)} груп...")

        valid_image_paths = [
            os.path.abspath(p) for p in self.image_paths if os.path.exists(p)
        ]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state="state.json")
            page = context.new_page()

            for idx, group_url in enumerate(groups, start=1):
                self.log(f"\n[{idx}/{len(groups)}] Перехід: {group_url}")
                try:
                    response = page.goto(
                        group_url, wait_until="domcontentloaded", timeout=15000
                    )
                    page.wait_for_timeout(3000)

                    page_content = page.content().lower()
                    if (
                            (response and response.status == 404)
                            or "this content isn't available" in page_content
                            or "вміст недоступний" in page_content
                    ):
                        self.log(
                            f"⚠️ ПОПЕРЕДЖЕННЯ: Групу не знайдено або її видалено ({group_url}). Переходимо далі..."
                        )
                        continue

                    self.log("Шукаємо поле для введення...")
                    post_box = page.get_by_text("Напишіть щось...")

                    if not post_box.is_visible(timeout=4000):
                        post_box = page.get_by_text("Write something...")

                    if not post_box.is_visible(timeout=2000):
                        self.log(
                            f"⚠️ ПОПЕРЕДЖЕННЯ: Поле публікації не знайдено у {group_url}. Переходимо далі..."
                        )
                        continue

                    post_box.click()
                    page.wait_for_timeout(2000)

                    # Завантаження фото через expectant FileChooser
                    if valid_image_paths:
                        self.log(
                            f"Завантажуємо фото ({len(valid_image_paths)} шт.)..."
                        )

                        # Спочатку шукаємо кнопку додавання фото всередині діалогу
                        photo_btn = page.locator(
                            "div[aria-label*='Фото/відео'], div[aria-label*='Photo/video'], div[aria-label*='Світлина/відео']"
                        ).first

                        if photo_btn.is_visible(timeout=3000):
                            # Використовуємо expect_file_chooser перед кліком
                            with page.expect_file_chooser(timeout=5000) as fc_info:
                                photo_btn.click()
                            file_chooser = fc_info.value
                            file_chooser.set_files(valid_image_paths)
                        else:
                            # Альтернативний фолбек через безпосереднє встановлення файлів у будь-який наявний input
                            file_input = page.locator("input[type='file']").first
                            file_input.evaluate("el => el.setAttribute('multiple', 'true')")
                            file_input.set_input_files(valid_image_paths)

                        # Даємо час Facebook провантажити та прорендерити прев'ю фото
                        wait_time = 6000 + (len(valid_image_paths) * 2500)
                        self.log("Чекаємо завантаження прев'ю фото у FB...")
                        page.wait_for_timeout(wait_time)

                    if post_text:
                        self.log("Вводимо текст...")
                        page.keyboard.type(post_text, delay=40)
                        page.wait_for_timeout(1000)

                    self.log("Публікуємо...")
                    publish_btn = page.get_by_role("button", name="Опублікувати")
                    if not publish_btn.is_visible(timeout=2000):
                        publish_btn = page.get_by_role("button", name="Post")

                    publish_btn.click()

                    # Затримка для завершення публікації
                    page.wait_for_timeout(10000)
                    self.log("Успішно опубліковано!")

                except Exception as e:
                    self.log(
                        f"❌ ПОМИЛКА під час обробки {group_url}: {e}\nПродовжуємо публікацію в інші групи..."
                    )

                if idx < len(groups):
                    delay = random.randint(40, 60)
                    self.log(f"Пауза {delay} секунд...")
                    time.sleep(delay)

            browser.close()
            self.log("\nУсі публікації завершено!")

        self.btn_start.configure(state="normal")


if __name__ == "__main__":
    app = FBAutoPosterApp()
    app.mainloop()