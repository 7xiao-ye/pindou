import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import io
import numpy as np
from typing import List, Tuple, Optional, Dict, Set

def split_image(img: Image.Image, rows: int, cols: int) -> Image.Image:
    """Split image into grid with enhanced grid lines and shadows"""
    width, height = img.size
    cell_width = width // cols
    cell_height = height // rows
    
    result = Image.new('RGB', (width, height))
    result.paste(img, (0, 0))
    
    draw = ImageDraw.Draw(result)
    
    line_width = 1
    for i in range(1, rows):
        y = i * cell_height
        draw.line([(0, y), (width, y)], fill='white', width=line_width)
    
    for i in range(1, cols):
        x = i * cell_width
        draw.line([(x, 0), (x, height)], fill='white', width=line_width)
    
    draw.rectangle([0, 0, width-1, height-1], outline='white', width=line_width)
    
    return result

def get_cell_colors(img: Image.Image, rows: int, cols: int) -> List[List[Tuple[int, int, int]]]:
    """Extract dominant color from each cell using numpy"""
    width, height = img.size
    cell_width = width // cols
    cell_height = height // rows
    
    img_array = np.array(img)
    colors = []
    
    for row in range(rows):
        row_colors = []
        for col in range(cols):
            x = col * cell_width
            y = row * cell_height
            cell = img_array[y:y+cell_height, x:x+cell_width]
            avg_color = cell.mean(axis=(0, 1)).astype(int)
            row_colors.append(tuple(avg_color))
        colors.append(row_colors)
    return colors

def get_unique_colors(cell_colors: List[List[Tuple[int, int, int]]]) -> List[Tuple[int, int, int]]:
    """Extract unique colors from cell colors"""
    unique_colors: Set[Tuple[int, int, int]] = set()
    for row in cell_colors:
        for color in row:
            unique_colors.add(color)
    return list(unique_colors)[:12]

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def create_game_board(rows: int, cols: int, user_colors: Optional[List[List[str]]] = None, cell_size: int = 30) -> Image.Image:
    """Create a game board with transparent background and custom cell size"""
    width = cols * cell_size
    height = rows * cell_size
    
    board = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(board)
    
    for row in range(rows):
        for col in range(cols):
            x = col * cell_size
            y = row * cell_size
            
            if user_colors and user_colors[row][col]:
                color = user_colors[row][col]
            else:
                color = (255, 255, 255, 128)
            
            draw.rectangle([x + 2, y + 2, x + cell_size, y + cell_size], fill=(0, 0, 0, 30))
            draw.rectangle([x, y, x + cell_size - 2, y + cell_size - 2], 
                         fill=color, outline='black', width=1)
    
    return board

def resize_image(img: Image.Image, max_size: int = 800) -> Image.Image:
    """Resize image to fit within max_size"""
    width, height = img.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int((max_size / width) * height)
        else:
            new_height = max_size
            new_width = int((max_size / height) * width)
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return img

def get_color_name(hex_color: str) -> str:
    """Get color name from hex code"""
    color_names = {
        '#FF6B6B': '珊瑚红',
        '#4ECDC4': '青绿色',
        '#45B7D1': '天蓝色',
        '#96CEB4': '薄荷绿',
        '#FFEAA7': '柠檬黄',
        '#DDA0DD': '薰衣草',
        '#98D8C8': '蓝绿色',
        '#F7DC6F': '金黄色',
        '#BB8FCE': '淡紫色',
        '#85C1E9': '浅蓝色',
        '#F1948A': '浅珊瑚',
        '#82E0AA': '嫩绿色'
    }
    return color_names.get(hex_color, '自定义')

def main():
    st.set_page_config(page_title="玩拼豆 - 优化版", page_icon="🎨", layout="wide")
    
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        h1 {
            color: #2c3e50;
            font-weight: 700;
        }
        h2 {
            color: #34495e;
            font-weight: 600;
        }
        .stSlider {
            padding: 10px 0;
        }
        .stFileUploader {
            margin: 10px 0;
        }
        .page-container {
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)
    
    default_states = {
        'uploaded_img': None,
        'processed_img': None,
        'cell_colors': None,
        'unique_colors': None,
        'user_colors': None,
        'current_page': 'upload',
        'rows': 10,
        'cols': 10,
        'selected_color': '#FF6B6B',
        'max_size': 800
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    def go_to_page(page: str):
        st.session_state.current_page = page
    
    if st.session_state.current_page == 'upload':
        st.title("🎨 玩拼豆 - 优化版")
        
        st.header("1. 上传图片")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "选择一张图片", 
                type=['png', 'jpg', 'jpeg'],
                help="支持 PNG、JPG、JPEG 格式的图片"
            )
        
        with col2:
            st.session_state.max_size = st.slider(
                "图片最大尺寸", 
                min_value=400, 
                max_value=1200, 
                value=st.session_state.max_size, 
                step=100,
                help="调整处理后图片的最大尺寸"
            )
        
        if uploaded_file is not None:
            try:
                img = Image.open(uploaded_file)
                img = resize_image(img, st.session_state.max_size)
                st.session_state.uploaded_img = img
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("原图")
                    st.image(img, use_container_width=True)
                
                st.header("2. 网格设置")
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.rows = st.slider(
                        "行数", 
                        min_value=2, 
                        max_value=100, 
                        value=st.session_state.rows,
                        help="设置网格的行数"
                    )
                with col2:
                    st.session_state.cols = st.slider(
                        "列数", 
                        min_value=2, 
                        max_value=100, 
                        value=st.session_state.cols,
                        help="设置网格的列数"
                    )
                
                if st.button("生成拼豆图片", type="primary", use_container_width=True):
                    with st.spinner('处理中...'):
                        processed_img = split_image(img, st.session_state.rows, st.session_state.cols)
                        st.session_state.processed_img = processed_img
                        st.session_state.cell_colors = get_cell_colors(img, st.session_state.rows, st.session_state.cols)
                        st.session_state.unique_colors = get_unique_colors(st.session_state.cell_colors)
                        go_to_page('process')
            except Exception as e:
                st.error(f"图片处理失败: {str(e)}")
    
    elif st.session_state.current_page == 'process':
        st.title("🎨 玩拼豆 - 优化版")
        
        if st.button("← 返回上传", use_container_width=True):
            go_to_page('upload')
        
        st.header("3. 拼豆图片")
        col1, col2 = st.columns(2)
        with col1:
            st.image(st.session_state.processed_img, use_container_width=True)
        
        with col2:
            st.subheader("处理信息")
            st.info(f"网格大小: {st.session_state.rows} × {st.session_state.cols}")
            st.info(f"图片尺寸: {st.session_state.processed_img.size[0]} × {st.session_state.processed_img.size[1]} 像素")
        
        buf = io.BytesIO()
        st.session_state.processed_img.save(buf, format='PNG')
        byte_im = buf.getvalue()
        st.download_button(
            label="💾 保存图片",
            data=byte_im,
            file_name="bead_pattern.png",
            mime="image/png",
            use_container_width=True,
            help="下载生成的拼豆图片"
        )
        
        st.header("4. 提取的色彩")
        st.subheader("从图片中提取的主要色彩（点击选择颜色）")
        
        color_cols = st.columns(6)
        for i, color in enumerate(st.session_state.unique_colors):
            with color_cols[i % 6]:
                hex_color = rgb_to_hex(color)
                if st.button(
                    f" ", 
                    key=f"color_{i}",
                    help=hex_color,
                    kwargs={"style": {
                        "background-color": hex_color, 
                        "width": "50px", 
                        "height": "50px", 
                        "border-radius": "8px", 
                        "border": "2px solid #333", 
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.2)"
                    }}
                ):
                    st.session_state.selected_color = hex_color
        
        if st.button("🎮 开始游戏", type="primary", use_container_width=True):
            st.session_state.user_colors = [[None for _ in range(st.session_state.cols)] for _ in range(st.session_state.rows)]
            go_to_page('game')
    
    elif st.session_state.current_page == 'game':
        st.title("🎨 玩拼豆 - 优化版")
        
        if st.button("← 返回处理", use_container_width=True):
            go_to_page('process')
        
        st.header("5. 拼豆游戏")
        
        st.subheader("选择颜色")
        
        custom_color = st.color_picker("自定义颜色", st.session_state.selected_color)
        if custom_color != st.session_state.selected_color:
            st.session_state.selected_color = custom_color
        
        st.subheader("图片提取的颜色（点击选择）")
        color_cols = st.columns(6)
        for i, color in enumerate(st.session_state.unique_colors):
            with color_cols[i % 6]:
                hex_color = rgb_to_hex(color)
                if st.button(
                    f" ", 
                    key=f"game_color_{i}",
                    help=hex_color,
                    kwargs={"style": {
                        "background-color": hex_color, 
                        "width": "50px", 
                        "height": "50px", 
                        "border-radius": "8px", 
                        "border": "2px solid #333", 
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.2)"
                    }}
                ):
                    st.session_state.selected_color = hex_color
        
        st.info(f"当前选择的颜色: {get_color_name(st.session_state.selected_color)} ({st.session_state.selected_color})")
        
        st.subheader("游戏区域")
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.subheader("原图对照")
            small_img = st.session_state.processed_img.resize(
                (int(st.session_state.processed_img.width * 0.8), 
                 int(st.session_state.processed_img.height * 0.8)),
                Image.Resampling.LANCZOS
            )
            st.image(small_img, use_container_width=True)
        
        with col2:
            st.subheader("作品预览（点击格子染色）")
            cell_size = max(20, min(40, 300 // max(st.session_state.rows, st.session_state.cols)))
            game_board = create_game_board(
                st.session_state.rows, 
                st.session_state.cols,
                user_colors=st.session_state.user_colors,
                cell_size=cell_size
            )
            
            game_container = st.container()
            with game_container:
                for row in range(st.session_state.rows):
                    cols_list = st.columns(st.session_state.cols, gap="small")
                    for col in range(st.session_state.cols):
                        with cols_list[col]:
                            current_color = st.session_state.user_colors[row][col] or 'rgba(255,255,255,0.5)'
                            if st.button(
                                " ",
                                key=f"cell_{row}_{col}",
                                help=f"({row}, {col})",
                                kwargs={"style": {
                                    "background-color": current_color, 
                                    "border-radius": "4px", 
                                    "border": "1px solid #333",
                                    "padding": "0",
                                    "min-width": "20px",
                                    "min-height": "20px"
                                }}
                            ):
                                st.session_state.user_colors[row][col] = st.session_state.selected_color
                                st.rerun()
            
            st.image(game_board, use_container_width=True)
        
        st.subheader("游戏控制")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 重置", use_container_width=True):
                st.session_state.user_colors = [[None for _ in range(st.session_state.cols)] for _ in range(st.session_state.rows)]
                st.rerun()
        
        with col2:
            if st.button("🎨 自动填充", use_container_width=True):
                if st.session_state.cell_colors:
                    hex_colors = []
                    for row in st.session_state.cell_colors:
                        hex_row = []
                        for rgb in row:
                            hex_color = rgb_to_hex(rgb)
                            hex_row.append(hex_color)
                        hex_colors.append(hex_row)
                    st.session_state.user_colors = hex_colors
                    st.rerun()
                else:
                    st.warning("无法自动填充，请先生成拼豆图片")
        
        with col3:
            buf = io.BytesIO()
            game_board = create_game_board(
                st.session_state.rows, 
                st.session_state.cols,
                user_colors=st.session_state.user_colors
            )
            game_board.save(buf, format='PNG')
            byte_im = buf.getvalue()
            st.download_button(
                label="💾 保存结果",
                data=byte_im,
                file_name="bead_game_result.png",
                mime="image/png",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
