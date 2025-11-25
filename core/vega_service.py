"""
Vega渲染服务
渲染Vega-Lite规范为图像
注意：需要Node.js环境和vega-cli
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any
import tempfile
import base64
import copy

from config.settings import Settings
from core.utils import app_logger, encode_image_to_base64

# 尝试导入 altair 作为替代渲染方案
try:
    import altair as alt
    import vl_convert as vlc
    ALTAIR_AVAILABLE = True
except ImportError:
    ALTAIR_AVAILABLE = False


class VegaService:
    """Vega渲染服务"""
    
    def __init__(self):
        self.default_width = Settings.VEGA_DEFAULT_WIDTH
        self.default_height = Settings.VEGA_DEFAULT_HEIGHT
        self.require_cli = Settings.VEGA_REQUIRE_CLI
        self._check_rendering_capabilities()
        app_logger.info("Vega Service initialized")
    
    def _check_rendering_capabilities(self):
        """检查可用的渲染方案"""
        self.vega_cli_available = False
        self.altair_available = ALTAIR_AVAILABLE
        
        # 检查 vega-cli 是否可用
        try:
            result = subprocess.run(
                ['vl2png', '--version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self.vega_cli_available = True
                version = result.stdout.decode('utf-8').strip()
                app_logger.info(f"✅ vega-cli available: {version}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 如果要求必须使用 CLI 但 CLI 不可用
        if self.require_cli and not self.vega_cli_available:
            error_msg = (
                "\n" + "="*70 + "\n"
                "❌ ERROR: VEGA_REQUIRE_CLI is set but vega-cli is not available!\n"
                "="*70 + "\n"
                "\n"
                "vega-cli is required but not found in your system.\n"
                "Please install Node.js and vega-cli to continue.\n"
                "\n"
                "Quick Installation Guide:\n"
                "\n"
                "macOS:\n"
                "  brew install node\n"
                "  npm install -g vega vega-lite vega-cli canvas\n"
                "\n"
                "Ubuntu/Debian:\n"
                "  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -\n"
                "  sudo apt-get install -y nodejs\n"
                "  sudo apt-get install -y build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev\n"
                "  sudo npm install -g vega vega-lite vega-cli canvas\n"
                "\n"
                "Windows:\n"
                "  1. Download Node.js from https://nodejs.org/\n"
                "  2. Install Node.js\n"
                "  3. Open Command Prompt as Administrator\n"
                "  4. Run: npm install -g vega vega-lite vega-cli canvas\n"
                "\n"
                "After installation, verify with: vl2png --version\n"
                "\n"
                "For detailed instructions, see: NODEJS_VEGA_INSTALLATION.md\n"
                "="*70 + "\n"
            )
            app_logger.error(error_msg)
            raise RuntimeError(
                "vega-cli is required (VEGA_REQUIRE_CLI=True) but not found. "
                "Please install Node.js and vega-cli. See NODEJS_VEGA_INSTALLATION.md"
            )
        
        # 正常情况下的日志输出
        if not self.vega_cli_available:
            app_logger.warning("⚠️  vega-cli not found")
        
        # 报告可用的渲染方案
        if self.altair_available:
            app_logger.info("✅ altair/vl-convert available (Pure Python renderer)")
        
        if not self.vega_cli_available and not self.altair_available and not self.require_cli:
            app_logger.warning(
                "⚠️  WARNING: No chart renderer available!\n"
                "   System will use mock rendering (placeholder images).\n"
                "\n"
                "   To enable real chart rendering, choose one:\n"
                "\n"
                "   Option 1 - Pure Python (Recommended, No Node.js needed):\n"
                "   pip install altair vl-convert-python --break-system-packages\n"
                "\n"
                "   Option 2 - Node.js based (Higher quality):\n"
                "   1. Install Node.js from https://nodejs.org/\n"
                "   2. Run: npm install -g vega vega-lite vega-cli canvas\n"
                "\n"
                "   See documentation: NODEJS_VEGA_INSTALLATION.md\n"
            )
        elif not self.vega_cli_available and not self.require_cli:
            app_logger.info(
                "ℹ️  Using altair for rendering (Pure Python).\n"
                "   For better quality, consider installing vega-cli:\n"
                "   1. Install Node.js: https://nodejs.org/\n"
                "   2. Run: npm install -g vega vega-lite vega-cli canvas\n"
            )
    
    def render(self, vega_spec: Dict, output_format: str = "png") -> Dict[str, Any]:
        """
        渲染Vega-Lite规范为图像
        
        渲染优先级（当 VEGA_REQUIRE_CLI=False 时）:
        1. altair + vl-convert (纯Python，无需Node.js)
        2. vega-cli (需要Node.js)
        3. mock渲染 (占位符)
        
        当 VEGA_REQUIRE_CLI=True 时:
        - 只使用 vega-cli
        - 如果 vega-cli 不可用，返回错误
        
        Args:
            vega_spec: Vega-Lite JSON规范
            output_format: 输出格式 (png/svg)
        
        Returns:
            {
                "success": bool,
                "image_base64": str,  # base64编码的图像
                "image_path": str,  # 临时文件路径
                "renderer": str,  # 使用的渲染器
                "error": str
            }
        """
        try:
            # 如果要求只使用 CLI
            if self.require_cli:
                if not self.vega_cli_available:
                    return {
                        "success": False,
                        "error": "vega-cli is required but not available. Please install Node.js and vega-cli. See NODEJS_VEGA_INSTALLATION.md"
                    }
                # 只使用 vega-cli
                return self._render_with_cli(vega_spec, output_format)
            
            # 正常模式：尝试多种渲染方案
            # 方案 1: 使用 altair + vl-convert（纯 Python，推荐）
            if ALTAIR_AVAILABLE:
                try:
                    # 将 vega-lite spec 转换为图像
                    png_data = vlc.vegalite_to_png(
                        vega_spec,
                        scale=2  # 提高分辨率
                    )
                    
                    # 转换为 base64
                    image_base64 = base64.b64encode(png_data).decode('utf-8')
                    
                    app_logger.info("✅ Rendered using altair/vl-convert (Python)")
                    return {
                        "success": True,
                        "image_base64": image_base64,
                        "image_path": None,
                        "renderer": "altair"
                    }
                except Exception as e:
                    app_logger.warning(f"Altair rendering failed: {e}, trying vega-cli...")
            
            # 方案 2: 使用vega-cli (需要 Node.js)
            if self.vega_cli_available:
                return self._render_with_cli(vega_spec, output_format)
            
            # 方案 3: Mock 渲染（如果没有其他选项）
            app_logger.warning("No real renderer available, using mock rendering")
            return self._mock_render(vega_spec)
            
        except Exception as e:
            app_logger.error(f"Render error: {e}")
            return {"success": False, "error": str(e)}
    
    def _render_with_cli(self, vega_spec: Dict, output_format: str = "png") -> Dict[str, Any]:
        """使用 vega-cli 渲染"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as spec_file:
                json.dump(vega_spec, spec_file)
                spec_path = spec_file.name
            
            output_path = spec_path.replace('.json', f'.{output_format}')
            
            subprocess.run([
                'vl2png',
                spec_path,
                output_path
            ], check=True, capture_output=True, timeout=10)
            
            # 读取生成的图像
            image_base64 = encode_image_to_base64(output_path)
            
            app_logger.info("✅ Rendered using vega-cli (Node.js)")
            return {
                "success": True,
                "image_base64": image_base64,
                "image_path": output_path,
                "renderer": "vega-cli"
            }
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            error_msg = f"vega-cli execution failed: {e}"
            app_logger.error(error_msg)
            
            if self.require_cli:
                # 如果要求只使用 CLI，返回错误
                return {
                    "success": False,
                    "error": error_msg,
                    "help": "Please check vega-cli installation. Run: vl2png --version"
                }
            else:
                # 否则使用 mock 渲染
                app_logger.warning(
                    "❌ vega-cli not found. Using mock rendering.\n"
                    "\n"
                    "   Quick Fix - Install Node.js and vega-cli:\n"
                    "   macOS: brew install node && npm install -g vega vega-lite vega-cli canvas\n"
                    "   Windows: Download from https://nodejs.org/ then run:\n"
                    "            npm install -g vega vega-lite vega-cli canvas\n"
                    "\n"
                    "   OR install Python alternative (no Node.js needed):\n"
                    "   pip install altair vl-convert-python --break-system-packages\n"
                    "\n"
                    "   Full guide: See NODEJS_VEGA_INSTALLATION.md\n"
                )
                return self._mock_render(vega_spec)
    
    def _mock_render(self, vega_spec: Dict) -> Dict:
        """
        模拟渲染（返回占位符图像）
        
        当 vega-cli 和 altair 都不可用时使用
        """
        app_logger.info(
            "ℹ️  Using mock rendering (placeholder image).\n"
            "   For real charts, see VEGA_CLI_INSTALLATION.md"
        )
        
        # 返回一个简单的1x1像素占位符（白色）
        mock_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        return {
            "success": True,
            "image_base64": mock_image,
            "image_path": None,
            "renderer": "mock",
            "warning": "Using mock rendering. Install vega-cli or altair for real charts."
        }
    
    def validate_spec(self, vega_spec: Dict) -> Dict[str, Any]:
        """验证Vega-Lite规范"""
        required_fields = ["mark", "encoding"]
        missing = [f for f in required_fields if f not in vega_spec]
        
        if missing:
            return {
                "valid": False,
                "error": f"Missing required fields: {missing}"
            }
        return {"valid": True}
    
    def update_spec(self, vega_spec: Dict, updates: Dict) -> Dict:
        """更新Vega-Lite规范"""
        new_spec = copy.deepcopy(vega_spec)  # 使用copy.deepcopy代替JSON序列化
        new_spec.update(updates)
        return new_spec


_vega_service = None

def get_vega_service() -> VegaService:
    """获取Vega服务单例"""
    global _vega_service
    if _vega_service is None:
        _vega_service = VegaService()
    return _vega_service
