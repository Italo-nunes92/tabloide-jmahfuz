from pathlib import Path
import datetime
import pytz


SAO_PAULO_TZ = pytz.timezone('America/Sao_Paulo')
BASE_DIR = Path(__file__).resolve().parent
ERROS = BASE_DIR.parent / 'Logs'


def getDataHora():
    return datetime.datetime.now(SAO_PAULO_TZ).strftime('%d/%m/%Y %H:%M:%S')

def erro_log(msg):
    with open((ERROS / 'erro_log.txt'), 'a',encoding='utf8') as arquivo:
            arquivo.write(f'{getDataHora()} : {msg}\n')
            
def print_detailed(self):
    fields = self._meta.fields + self._meta.many_to_many
    details = []
    
    details.append(f"\n{'='*50}")
    details.append(f"Detalhes do Produto: {self.name}")
    details.append(f"{'='*50}")
    
    for field in fields:
        field_name = field.name
        field_value = getattr(self, field_name)
        
        if field.is_relation:
            if field.many_to_many:
                related_objects = field_value.all()
                value_str = ', '.join([str(obj) for obj in related_objects])
            else:
                value_str = str(field_value)
        else:
            value_str = str(field_value)
            
        details.append(f"{field_name}: {value_str}")
    
    details.append(f"{'='*50}\n")
    text_log = '\n'.join(details)

    erro_log(text)
