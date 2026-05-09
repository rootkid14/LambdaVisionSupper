from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
from app.services.utils.image_utils import base64_to_cv2, cv2_to_base64
from typing import Any, List
import numpy as np
import cv2

# ==========================================
# 1. NODE: BASE64 -> CV2
# ==========================================
class Base64ToCV2Input(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute In
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    base64_image : Any = Field(default=None, title="Base64 Image", description=UIDataType.BASE64.value)

class Base64ToCV2Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute Out
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    cv2_image : np.ndarray = Field(default=None, title="CV2 Image", description=UIDataType.NUMPY_ARRAY.value)

@registry_node
class Base64ToCV2ConvertNode(BaseNode[Base64ToCV2Input, Base64ToCV2Output]):
    INPUT_SCHEMA = Base64ToCV2Input
    OUTPUT_SCHEMA = Base64ToCV2Output
    NODE_TYPE = NodeType.PROGRAM  # <--- THÊM NODE_TYPE (Type 1)
    UI_LABEL = "Base64 -> CV2"
    UI_DESCRIPTION = "Convert Base 64 Image to CV2 Image"
    UI_COLOR = "#1A5300"

    async def execute(self):
        result = base64_to_cv2(self.local_input.base64_image)
        # Bổ sung truyền giá trị cho execute_out
        self.local_output = self.OUTPUT_SCHEMA(execute_out="GO", cv2_image=result)


# ==========================================
# 2. NODE: CV2 -> BASE64
# ==========================================
class CV2ToBase64Input(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute In
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    cv2_image : np.ndarray = Field(default=None, title="CV2 Image", description=UIDataType.NUMPY_ARRAY.value)
    
class CV2ToBase64Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute Out
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    base64_image : Any = Field(default=None, title="Base64 Image", description=UIDataType.BASE64.value)
    
@registry_node
class CV2ToBase64ConvertNode(BaseNode[CV2ToBase64Input, CV2ToBase64Output]):
    INPUT_SCHEMA = CV2ToBase64Input
    OUTPUT_SCHEMA = CV2ToBase64Output
    NODE_TYPE = NodeType.PROGRAM  # <--- THÊM NODE_TYPE (Type 1)
    UI_LABEL = "CV2 --> Base64"
    UI_DESCRIPTION = "Convert CV2 to Base64 Image"
    UI_COLOR = "#9E5400"

    async def execute(self):
        result = cv2_to_base64(self.local_input.cv2_image)
        # Bổ sung truyền giá trị cho execute_out
        self.local_output = self.OUTPUT_SCHEMA(execute_out="GO", base64_image=result)


class ImageResizeInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    input_image : Any = Field(default=None, title="Input Image", description=UIDataType.ANY.value)
    width : float = Field(default=500, title="Width", description=UIDataType.NUMBER.value)
    height : float = Field(default=500, title="Height", description=UIDataType.NUMBER.value)

class ImageResizeOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    ouput_image : Any = Field(default=None, title="Output Image", description=UIDataType.ANY.value)

@registry_node
class ImageResize(BaseNode[ImageResizeInput, ImageResizeOutput]):
    INPUT_SCHEMA = ImageResizeInput
    OUTPUT_SCHEMA = ImageResizeOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Image Resize"
    UI_DESCRIPTION = "Resize an image"
    UI_COLOR = "#202020"
    REQUIRE_TIMEOUT = False

    CONFIG_FIELDS = [
        UIConfigField(
            id="Format",
            label="Output Format",
            type= UIConfigType.SELECT,
            options=["B64", "CV2"],
            default="CV2"
        )
    ]

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        self.output_format = self.get_config_field_value("Format")

    def extract_cv2_image(image_input: Any) -> np.ndarray:
        if isinstance(image_input, np.ndarray):
            return image_input.copy()
        elif isinstance(image_input, str):
            return base64_to_cv2(image_input)
        else:
            raise ValueError("Đầu vào không phải là Numpy Array hoặc Base64 String hợp lệ.")

    async def execute(self):
        img = self.extract_cv2_image(self.local_input.input_image)

        out_img = cv2.resize(img, (self.local_input.width, self.local_input.height))

        if self.output_format == "B64":
            out_img = cv2_to_base64(out_img)

        self.local_output = self.OUTPUT_SCHEMA(ouput_image=out_img)
    

class BBoxesWarpAffineInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    boundingboxes_coords : list = Field(default=[], title="BBoxes Coords", description=UIDataType.LIST.value) # Format [x_min, y_min, w, h]
    anchor_points : List[list] = Field(default=[], title="Anchor Points", description=UIDataType.LIST.value)
    actual_points : List[list] = Field(default=[], title="Actual Anchors", description=UIDataType.LIST.value)



class BBoxesWarpAffineOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    new_bboxes_coords : Any = Field(default=[], title="New BBoxes Coords", description=UIDataType.LIST.value)

@registry_node
class BBoxesWarpAffine(BaseNode[BBoxesWarpAffineInput, BBoxesWarpAffineOutput]):
    INPUT_SCHEMA = BBoxesWarpAffineInput
    OUTPUT_SCHEMA = BBoxesWarpAffineOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Warp Affine"
    UI_DESCRIPTION = "Transforms bounding boxes coordinates to follow 3 warp affine anchors"
    UI_COLOR = "#202020"
    REQUIRE_TIMEOUT = False

    async def execute(self):
        if(len(self.local_input.actual_points) != 3):
            raise ValueError(f"There is not enough anchor points for caliberation")

        src_pts = np.array(self.local_input.anchor_points, dtype=np.float32)
        dst_pts = np.array(self.local_input.actual_points, dtype=np.float32)

        # 2. Truyền Numpy Array vào OpenCV
        M = cv2.getAffineTransform(src_pts, dst_pts)

        centers_old = []
        for bboxes in self.local_input.boundingboxes_coords:
            x_min, y_min, w, h = bboxes
            cx = x_min + w / 2.0
            cy = y_min + h / 2.0
            centers_old.append([cx, cy])

        centers_old_np = np.array(centers_old, dtype=np.float32).reshape(-1, 1, 2)

        centers_new_np = cv2.transform(centers_old_np, M)

        bboxes_new = []
        for i in range(len(self.local_input.boundingboxes_coords)):
            # Lấy tọa độ tâm mới
            new_cx = centers_new_np[i][0][0]
            new_cy = centers_new_np[i][0][1]
            
            # Lấy lại width và height cũ của box tương ứng
            w = self.local_input.boundingboxes_coords[i][2]
            h = self.local_input.boundingboxes_coords[i][3]
            
            # Tính toán lại x_min, y_min
            new_xmin = int(round(new_cx - w / 2.0))
            new_ymin = int(round(new_cy - h / 2.0))
            
            # Thêm vào danh sách mới
            bboxes_new.append([new_xmin, new_ymin, w, h])

        self.local_output = self.OUTPUT_SCHEMA(new_bboxes_coords=bboxes_new)

        