import flet as ft
import re

def main(page: ft.Page):
    # 기본 페이지 설정
    page.title = "업무일지 스마트 검색"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # ---------------------------------------------------
    # 1. 내부 기억장치에서 기존 파일 데이터 불러오기
    # ---------------------------------------------------
    log_content = page.client_storage.get("log_content") or ""
    log_filename = page.client_storage.get("log_filename") or ""
    current_search_results = []

    # ---------------------------------------------------
    # 2. 화면 UI 구성 요소들 준비
    # ---------------------------------------------------
    title = ft.Text("🔍 업무일지 스마트 검색", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
    
    file_status = ft.Text(
        f"📁 현재 저장된 파일: {log_filename}" if log_filename else "📁 선택된 파일이 없습니다.", 
        color=ft.colors.GREEN_700 if log_filename else ft.colors.RED,
        weight=ft.FontWeight.BOLD,
        size=16
    )
    
    search_input = ft.TextField(
        label="검색어를 입력하세요", 
        border_color=ft.colors.BLUE,
        focused_border_color=ft.colors.BLUE_700
    )
    
    result_count = ft.Text(
        "✅ 파일이 기억되어 있습니다. 바로 검색을 시작하세요!" if log_content else "✅ 검색을 위해 파일을 먼저 선택해주세요.", 
        size=16, 
        weight=ft.FontWeight.BOLD
    )
    
    result_view = ft.Column(spacing=15)

    # ---------------------------------------------------
    # 3. 기능: 파일 선택 및 스마트폰에 영구 저장
    # ---------------------------------------------------
    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal log_content, log_filename
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            file_name = e.files[0].name
            try:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        log_content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, "r", encoding="cp949") as f:
                        log_content = f.read()
                
                log_filename = file_name
                page.client_storage.set("log_content", log_content)
                page.client_storage.set("log_filename", log_filename)
                
                file_status.value = f"📁 파일 업데이트 완료: {log_filename}"
                file_status.color = ft.colors.GREEN_700
                result_count.value = "✅ 파일이 성공적으로 기억되었습니다. 검색해보세요!"
                result_view.controls.clear()
                page.update()
            except Exception as ex:
                file_status.value = f"❌ 파일 읽기 오류: {str(ex)}"
                file_status.color = ft.colors.RED
                page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # ---------------------------------------------------
    # 4. 기능: 스마트 검색 및 추출 (새로운 로직 적용)
    # ---------------------------------------------------
    def search_click(e):
        nonlocal current_search_results
        keyword = search_input.value.strip()
        
        if not log_content:
            result_count.value = "❌ 업무일지 파일을 먼저 선택해주세요!"
            result_count.color = ft.colors.RED
            page.update()
            return
            
        if not keyword:
            result_count.value = "❌ 검색어를 입력해주세요!"
            result_count.color = ft.colors.RED
            page.update()
            return

        blocks = []
        curr_date = ""
        curr_block = []

        # 한 줄씩 읽으면서 똑똑하게 덩어리 나누기
        for line in log_content.split('\n'):
            original_line = line
            stripped = line.strip()
            
            # 빈 줄은 무시 (새로운 문단은 들여쓰기 여부로 판단)
            if not stripped:
                continue

            # 1. 날짜 확인 (예: 2026/10/5월)
            if re.match(r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}', stripped):
                if curr_block:
                    blocks.append((curr_date, curr_block))
                curr_date = stripped
                curr_block = []
                continue

            # 2. 들여쓰기(탭 또는 띄어쓰기) 여부 확인
            is_indented = original_line.startswith(' ') or original_line.startswith('\t')

            if not is_indented:
                # 들여쓰기가 없는 줄 -> 무조건 '새로운 제목'으로 취급하여 덩어리를 분리!
                if curr_block:
                    blocks.append((curr_date, curr_block))
                curr_block = [original_line.rstrip('\r\n')]
            else:
                # 들여쓰기가 있는 줄 -> 바로 직전 제목의 '본문'으로 추가
                curr_block.append(original_line.rstrip('\r\n'))

        # 마지막 덩어리 저장
        if curr_block:
            blocks.append((curr_date, curr_block))
            
        # 검색어 매칭하기
        found_blocks = []
        for date, block_lines in blocks:
            clean_block = "\n".join(block_lines)
            
            # 검색어가 이 덩어리에 포함되어 있다면 결과에 추가
            if keyword in clean_block:
                full_text = f"{date}\n{clean_block}" if date else clean_block
                found_blocks.append(full_text)
        
        current_search_results = found_blocks
        
        # 화면에 결과 출력
        result_view.controls.clear()
        if found_blocks:
            result_count.value = f"✅ 총 {len(found_blocks)}개의 항목을 찾았습니다!"
            result_count.color = ft.colors.GREEN_700
            for fb in found_blocks:
                result_view.controls.append(
                    ft.Container(
                        content=ft.Text(fb, size=16),
                        padding=15,
                        border=ft.border.all(1, ft.colors.BLUE_200),
                        border_radius=8,
                        bgcolor=ft.colors.BLUE_50
                    )
                )
        else:
            result_count.value = "❌ 검색 결과가 없습니다."
            result_count.color = ft.colors.RED

        page.update()

    # ---------------------------------------------------
    # 5. 기능: 검색 결과 클립보드 복사
    # ---------------------------------------------------
    def copy_click(e):
        if not current_search_results:
            page.snack_bar = ft.SnackBar(ft.Text("❌ 복사할 검색 결과가 없습니다."))
            page.snack_bar.open = True
            page.update()
            return
        
        result_text = "\n\n".join(current_search_results)
        page.set_clipboard(result_text)
        
        page.snack_bar = ft.SnackBar(
            ft.Text("✅ 검색 결과가 복사되었습니다! 카카오톡이나 메모장에 붙여넣기 하세요."),
            bgcolor=ft.colors.GREEN_700
        )
        page.snack_bar.open = True
        page.update()

    # ---------------------------------------------------
    # 6. 화면에 배치
    # ---------------------------------------------------
    page.add(
        title,
        ft.Divider(),
        ft.ElevatedButton(
            "📄 1. 업무일지 파일 선택하기 (최초 1회만)", 
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: file_picker.pick_files(allow_multiple=False),
            height=45
        ),
        file_status,
        ft.Divider(),
        search_input,
        ft.Row([
            ft.ElevatedButton("🔍 2. 검색하기", on_click=search_click, bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE, height=45),
            ft.ElevatedButton("📋 3. 결과 복사", on_click=copy_click, bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE, height=45),
        ], wrap=True),
        ft.Divider(),
        result_count,
        result_view
    )

ft.app(target=main)
