from enum import Flag, auto

class BlendType(Flag):
    SRC_MASK_1 = auto()
    SRC_MASK_NA = auto()
    SRC_MASK_A = auto()
    DST_MASK_1 = auto()
    DST_MASK_NA = auto()
    DST_MASK_A = auto()
    CLEAR = auto()
    SOURCE = SRC_MASK_1
    DESTINATION = DST_MASK_1
    OVER = SRC_MASK_1|DST_MASK_NA
    IN = SRC_MASK_A
    OUT = SRC_MASK_NA
    ATOP = SRC_MASK_A|DST_MASK_NA
    XOR = SRC_MASK_NA|DST_MASK_NA
    PLUS = SRC_MASK_1|DST_MASK_1
    
def alpha_blend(src_rgb,src_a,dst_rgb,dst_a,blend_type=BlendType.OVER):
    src_f=0
    if BlendType.SRC_MASK_1 in blend_type:
        src_f=1
    elif BlendType.SRC_MASK_NA in blend_type:
        src_f=1-dst_a
    elif  BlendType.SRC_MASK_A in blend_type:
        src_f=dst_a
    dst_f=0
    if  BlendType.DST_MASK_1 in blend_type:
        dst_f=1
    elif BlendType.DST_MASK_NA in blend_type:
        dst_f=1-src_a
    elif BlendType.DST_MASK_A in blend_type:
        dst_f=src_a
    out_a = src_a*src_f+dst_a*dst_f
    out_rgb=[]
    for (src_x,dst_x) in zip(src_rgb,dst_rgb):
        out_x=(src_x*src_a*src_f+dst_x*dst_a*dst_f)/out_a
        out_rgb.append(out_x)
    return (tuple(out_rgb),out_a)


def alpha_unblend_s(src_a,dst_rgb,dst_a,out_rgb,blend_type=BlendType.OVER):
    src_f=0
    if BlendType.SRC_MASK_1 in blend_type:
        src_f=1
    elif BlendType.SRC_MASK_NA in blend_type:
        src_f=1-dst_a
    elif BlendType.SRC_MASK_A in blend_type:
        src_f=dst_a
    dst_f=0
    if BlendType.DST_MASK_1 in blend_type:
        dst_f=1
    elif BlendType.DST_MASK_NA in blend_type:
        dst_f=1-src_a
    elif BlendType.DST_MASK_A in blend_type:
        dst_f=src_a
    out_a = src_a*src_f+dst_a*dst_f
    src_rgb=[]
    for (dst_x,out_x) in zip(dst_rgb,out_rgb):
        src_x=(out_x*out_a-dst_x*dst_a*dst_f)/(src_a*src_f)
        src_rgb.append(src_x)
    return (tuple(src_rgb),out_a)

def get_rgba_with_fixed_alhpa(rgb,alpha):
    (src_rgb,out_a)=alpha_unblend_s(alpha,(1,1,1),1,rgb,blend_type=BlendType.OVER)
    return tuple([c for c in src_rgb]+[alpha])

class CUD_V3():
    # CUD ver 3
    ALPHA=0.6
    # 赤
    A1 = (255/255, 40/255, 0/255)
    # 黄色
    A2 = (250/255, 245/255, 0/255)
    # 緑
    A3 = (53/255, 161/255, 107/255)
    # 青
    A4 = (0/255, 65/255, 255/255)
    # 空色
    A5 = (102/255, 204/255, 255/255)
    # ピンク
    A6 = (255/255, 153/255, 160/255)
    # オレンジ
    A7 = (255/255, 153/255, 0/255)
    # 紫
    A8 = (154/255, 0/255, 121/255)
    # 茶
    A9 = (102/255, 51/255, 0/255)
    # 明るいピンク
    B1 = (255/255, 209/255, 209/255)
    B1A = get_rgba_with_fixed_alhpa(B1,ALPHA)
    # クリーム
    B2 = (255/255, 255/255, 153/255)
    B2A = get_rgba_with_fixed_alhpa(B2,ALPHA)
    # 明るい黄緑
    B3 = (203/255, 242/255, 102/255)
    B3A = get_rgba_with_fixed_alhpa(B3,ALPHA)
    # 明るい空色
    B4 = (180/255, 235/255, 250/255)
    B4A = get_rgba_with_fixed_alhpa(B4,ALPHA)
    # ベージュ
    B5 = (237/255, 197/255, 143/255)
    B5A = get_rgba_with_fixed_alhpa(B5,ALPHA)
    # 明るい緑
    B6 = (135/255, 231/255, 176/255)
    B6A = get_rgba_with_fixed_alhpa(B6,ALPHA)
    # 明るい紫
    B7 = (199/255, 178/255, 222/255)
    B7A = get_rgba_with_fixed_alhpa(B7,ALPHA)
    # 白
    G1 = (255/255, 255/255, 255/255)
    # 明るいグレー
    G2 = (200/255, 200/255, 203/255)
    # グレー
    G3 = (127/255, 135/255, 143/255)
    # 黒
    G4 = (0/255, 0/255, 0/255)
    
class CUD_V4():
    A1=(255/255,75/255,0/255)
    A2=(255/255,241/255,0/255)
    A3=(3/255,175/255,122/255)
    A4=(0/255,90/255,255/255)
    A5=(77/255,196/255,255/255)
    A6=(255/255,128/255,130/255)
    A7=(246/255,170/255,0/255)
    A8=(153/255,0/255,153/255)
    A9=(128/255,64/255,0/255)
    B1=(255/255,202/255,191/255)
    B2=(255/255,255/255,128/255)
    B3=(216/255,242/255,85/255)
    B4=(191/255,228/255,255/255)
    B5=(255/255,202/255,128/255)
    B6=(119/255,217/255,168/255)
    B7=(201/255,172/255,230/255)
    G1 = (255/255, 255/255, 255/255)
    G2 = (200/255, 200/255, 203/255)
    G3 = (132/255, 145/255, 158/255)
    G4 = (0/255, 0/255, 0/255)
    ALPHA=0.667
    B1A = get_rgba_with_fixed_alhpa(B1,ALPHA)
    B2A = get_rgba_with_fixed_alhpa(B2,ALPHA)
    B3A = get_rgba_with_fixed_alhpa(B3,ALPHA)
    B4A = get_rgba_with_fixed_alhpa(B4,ALPHA)
    B5A = get_rgba_with_fixed_alhpa(B5,ALPHA)
    B6A = get_rgba_with_fixed_alhpa(B6,ALPHA)
    B7A = get_rgba_with_fixed_alhpa(B7,ALPHA)

    
class COLOR_PALLET:
    A6_1 = [7,2,3,4,5,9]
    A6_2 = [1,7,2,3,4,5]
    A6_3 = [1,7,2,3,8,5]
    A5_1 = [1,2,3,4,5]
    A5_2 = [7,2,3,5,8]
    A5_3 = [7,2,3,5,9]
    A5_4 = [7,2,4,5,9]
    A5_5 = [2,4,6,5,9]
    A4_1 = [1,2,3,5]
    A4_2 = [1,2,4,5]
    A4_3 = [1,3,4,5]
    A4_4 = [7,2,8,5]
    A4_5 = [7,3,8,5]
    A4_6 = [2,8,5,6]
    #B4_1 = [1,2,3,4]
    B4_2 = [1,2,4,7]
    B4_3 = [5,2,4,7]
    B3_1 = [1,2,4]
    B3_2 = [1,2,7]
    #B3_3 = [1,2,3]
    B3_4 = [2,6,4]
    #B3_5 = [2,6,3]
    B3_6 = [2,5,4]
    B3_7 = [2,5,7]
    A4B2_1 = [[7,2,4,9],[6,4]]
    A4B2_2 = [[7,3,5,9],[1,2]]
    A3B3_3 = [[7,3,9],[1,2,4]]
    A3B3_4 = [[7,3,9],[1,2,7]]
    A4B2_5 = [[7,4,5,9],[1,2]]
    A3B3_6 = [[7,4,9],[1,2,4]]
    A3B3_7 = [[7,4,9],[1,2,7]]
    A3B3_6 = [[7,4,9],[2,6,4]]


