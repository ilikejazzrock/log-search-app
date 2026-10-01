import flet as ft
import re

def main(page: ft.Page):
    # 앱 기본 테마 및 스크롤 설정
    page.title = "업무일지 검색기"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "adaptive"
    page.padding = 25

    # 1. UI 디자인: 제목
    title = ft.Text("🔍 업무일지 스마트 검색", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)

    # 2. UI 디자인: 파일 선택 구역
    file_path_data = {"path": ""}
    selected_file_text = ft.Text("📁 선택된 파일이 없습니다.", color=ft.colors.RED_500, size=13)

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path_data["path"] = e.files[0].path
            selected_file_text.value = f"📁 파일 선택됨: {e.files[0].name}"
            selected_file_text.color = ft.colors.GREEN_700
        else:
            file_path_data["path"] = ""
            selected_file_text.value = "📁 선택된 파일이 없습니다."
            selected_file_text.color = ft.colors.RED_500
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    file_btn = ft.ElevatedButton(
        text="1. 업무일지 파일 선택하기",
        icon=ft.icons.UPLOAD_FILE,
        bgcolor=ft.colors.GREY_200,
        color=ft.colors.BLACK87,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False)
    )

    # 3. UI 디자인: 검색어 입력 구역
    keyword_input = ft.TextField(
        label="검색어를 입력하세요",
        hint_text="예: 배터리",
        border_color=ft.colors.BLUE_400,
        width=350,
        autofocus=True
    )

    # 4. UI 디자인: 결과 출력 구역
    result_text = ft.Text("결과가 여기에 표시됩니다.", size=14, selectable=True)

    # 5. 검색 실행 로직
    def perform_search(e):
        input_file = file_path_data["path"]
        keyword = keyword_input.value.strip()

        if not input_file:
            result_text.value = "⚠️ 먼저 [업무일지 파일]을 선택해 주세요!"
            result_text.color = ft.colors.RED_500
            page.update()
            return

        if not keyword:
            result_text.value = "⚠️ 검색어를 입력해 주세요!"
            result_text.color = ft.colors.RED_500
            page.update()
            return

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            date_pattern = re.compile(r"^\d{4}/\d{1,2}/\d{1,2}")
            entries = []
            current_date_line = ""
            current_title_line = ""
            current_content_lines = []

            def save_entry():
                if current_date_line and current_title_line:
                    entries.append({
                        "date_line": current_date_line,
                        "title_line": current_title_line,
                        "content_lines": current_content_lines.copy()
                    })

            for line in lines:
                if not line.strip(): continue
                if date_pattern.match(line):
                    save_entry()
                    current_date_line = line.strip()
                    current_title_line = ""
                    current_content_lines = []
                elif not line.startswith('\t') and not line.startswith(' '):
                    save_entry()
                    current_title_line = line.strip()
                    current_content_lines = []
                else:
                    current_content_lines.append(line.rstrip('\n'))
            save_entry()

            match_count = 0
            display_text = ""

            for entry in entries:
                search_text = entry['title_line'] + " " + " ".join(entry['content_lines'])
                if keyword in search_text:
                    display_text += f"{entry['date_line']}\n{entry['title_line']}\n"
                    for content_line in entry['content_lines']:
                        display_text += f"{content_line}\n"
                    display_text += "\n"
                    match_count += 1

            if match_count > 0:
                result_text.value = f"✅ 총 {match_count}개의 항목을 찾았습니다!\n\n{display_text}"
                result_text.color = ft.colors.BLACK
            else:
                result_text.value = f"⚠️ '{keyword}'(이)가 포함된 내용을 찾을 수 없습니다."
                result_text.color = ft.colors.RED_500

        except Exception as ex:
            result_text.value = f"❌ 오류 발생: {ex}"
            result_text.color = ft.colors.RED_500

        page.update()

    # 파란색 검색 버튼
    search_btn = ft.ElevatedButton(
        text="2. 검색 및 추출하기",
        icon=ft.icons.SEARCH,
        bgcolor=ft.colors.BLUE_600,
        color=ft.colors.WHITE,
        width=350,
        height=50,
        on_click=perform_search
    )

    # 6. 화면에 레고 블록 조립하기
    page.add(
        ft.Column(
            [
                title,
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                file_btn,
                selected_file_text,
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                keyword_input,
                search_btn,
                ft.Divider(height=20, color=ft.colors.GREY_300),
                result_text
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

ft.app(target=main)
