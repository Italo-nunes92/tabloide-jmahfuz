from  django.core.exceptions import ValidationError

def validade_png(image):
    if not image.name.lower().endswith('.png'):
        raise ValidationError('Imagem deve ser PNG.')
    
def validade_svg(image):
    if not image.name.lower().endswith('.svg'):
        raise ValidationError('Imagem deve ser SVG.')