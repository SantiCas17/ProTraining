import os
import django
import gspread
from google.oauth2.service_account import Credentials
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import ExtractYear

# 1. Conectar con el entorno de Django (Asegurate de que 'protraining' sea el nombre de tu proyecto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from activities.models import RunActivity, CyclingActivity
from health.models import ErgometryTest

# 2. Configurar Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = 'google_credentials.json'

def get_sheet_client():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open("TrainingPro_Mobile")

def setup_worksheets(sheet):
    """Crea las pestañas si no existen"""
    nombres_requeridos = ['Run/Trail', 'Bicicleta', 'Salud', 'Historico']
    pestañas_actuales = [ws.title for ws in sheet.worksheets()]
    
    for nombre in nombres_requeridos:
        if nombre not in pestañas_actuales:
            sheet.add_worksheet(title=nombre, rows="100", cols="20")
            
def sync_deportes_mensual(sheet):
    """Actualiza las hojas de Run y Bici (Se resetea virtualmente cada mes)"""
    now = timezone.now()
    mes, anio = now.month, now.year
    
    # --- RUN/TRAIL ---
    ws_run = sheet.worksheet('Run/Trail')
    runs = RunActivity.objects.filter(date__year=anio, date__month=mes)
    
    km_totales = runs.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
    desnivel_total = runs.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0
    trail_km = runs.filter(is_trail=True).aggregate(Sum('distance_km'))['distance_km__sum'] or 0
    
    ws_run.clear()
    ws_run.update('A1:B4', [
        [f"Resumen Mensual: {mes}/{anio}", ""],
        ["Distancia Total (km)", round(km_totales, 1)],
        ["Desnivel Positivo (+m)", int(desnivel_total)],
        ["Específico Trail (km)", round(trail_km, 1)]
    ])
    
    # --- BICICLETA ---
    ws_bike = sheet.worksheet('Bicicleta')
    bikes = CyclingActivity.objects.filter(date__year=anio, date__month=mes)
    km_bici = bikes.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
    
    ws_bike.clear()
    ws_bike.update('A1:B2', [
        [f"Resumen Mensual: {mes}/{anio}", ""],
        ["Distancia Total (km)", round(km_bici, 1)]
    ])
    print(f"✅ Deportes mensuales sincronizados ({mes}/{anio})")

def sync_salud_evolutiva(sheet):
    """Agrega el último estudio de salud sin borrar los anteriores"""
    ws_salud = sheet.worksheet('Salud')
    
    if not ws_salud.acell('A1').value:
        ws_salud.append_row(["Fecha", "Peso (kg)", "IMC", "Estado", "Z1", "Z2", "Z3", "Z4", "Z5"])
        
    ultimo_test = ErgometryTest.objects.order_by('-date').first()
    
    if ultimo_test:
        fecha_str = ultimo_test.date.strftime("%d/%m/%Y")
        fechas_existentes = ws_salud.col_values(1)
        
        if fecha_str not in fechas_existentes:
            ws_salud.append_row([
                fecha_str,
                ultimo_test.weight_kg,
                ultimo_test.imc,
                ultimo_test.imc_status,
                f"{ultimo_test.z1_min}-{ultimo_test.z1_max}",
                f"{ultimo_test.z2_min}-{ultimo_test.z2_max}",
                f"{ultimo_test.z3_min}-{ultimo_test.z3_max}",
                f"{ultimo_test.z4_min}-{ultimo_test.z4_max}",
                f"{ultimo_test.z5_min}-{ultimo_test.z5_max}"
            ])
            print(f"✅ Salud sincronizada (Test del {fecha_str})")
        else:
            print("ℹ️ El último test de salud ya estaba registrado.")

def sync_historico_anual(sheet):
    """Genera un resumen anual histórico de todos los deportes"""
    ws_hist = sheet.worksheet('Historico')
    ws_hist.clear()
    ws_hist.update('A1:D1', [["Año", "Deporte", "Distancia Total (km)", "Desnivel Acumulado (+m)"]])
    
    runs = RunActivity.objects.annotate(year=ExtractYear('date')).values('year').annotate(km=Sum('distance_km'), elev=Sum('elevation_gain'))
    bikes = CyclingActivity.objects.annotate(year=ExtractYear('date')).values('year').annotate(km=Sum('distance_km'), elev=Sum('elevation_gain'))
    
    datos = []
    for r in runs:
        if r['year']:
            datos.append([r['year'], "Running & Trail", round(r['km'] or 0, 1), int(r['elev'] or 0)])
    for b in bikes:
        if b['year']:
            datos.append([b['year'], "Ciclismo", round(b['km'] or 0, 1), int(b['elev'] or 0)])
        
    # Ordenamos por año descendente para que lo más nuevo quede arriba
    datos = sorted(datos, key=lambda x: x[0], reverse=True)
    
    if datos:
        ws_hist.update(f'A2:D{len(datos) + 1}', datos)
        print("✅ Histórico anual sincronizado")

def main():
    print("Iniciando sincronización con Google Sheets...")
    try:
        sheet = get_sheet_client()
        setup_worksheets(sheet)
        
        sync_deportes_mensual(sheet)
        sync_salud_evolutiva(sheet)
        sync_historico_anual(sheet)
        
        print("🚀 ¡Sincronización completada con éxito!")
    except Exception as e:
        print(f"❌ Error en la sincronización: {e}")

if __name__ == '__main__':
    main()