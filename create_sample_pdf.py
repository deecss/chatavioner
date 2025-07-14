#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt demonstracyjny - tworzy przykładowy plik PDF z podstawowymi informacjami o lotnictwie
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

def create_sample_pdf():
    """Tworzy przykładowy PDF z podstawowymi informacjami lotniczymi"""
    
    # Utwórz katalog uploads jeśli nie istnieje
    os.makedirs('uploads', exist_ok=True)
    
    filename = 'uploads/sample_aviation_handbook.pdf'
    doc = SimpleDocTemplate(filename, pagesize=A4)
    
    # Style
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        spaceBefore=20
    )
    
    # Treść dokumentu
    story = []
    
    # Tytuł
    story.append(Paragraph("Podstawy Lotnictwa - Podręcznik Demonstracyjny", title_style))
    story.append(Spacer(1, 20))
    
    # Rozdział 1
    story.append(Paragraph("1. Zasady Lotu", heading_style))
    story.append(Paragraph("""
    Lot samolotu jest możliwy dzięki czterem podstawowym siłom: ciąg, opór, siła nośna i ciężar. 
    Ciąg generowany przez silnik pokonuje opór powietrza, podczas gdy siła nośna wytwarzana przez 
    skrzydła równoważy ciężar samolotu. Zasada Bernoulliego i trzecie prawo Newtona wyjaśniają 
    powstawanie siły nośnej.
    """, normal_style))
    
    story.append(Paragraph("""
    Kąt natarcia skrzydła ma kluczowe znaczenie dla wielkości siły nośnej. Zwiększenie kąta 
    natarcia do określonej granicy zwiększa siłę nośną, jednak przekroczenie kąta krytycznego 
    prowadzi do utraty ciągłości opływu i przeciągnięcia.
    """, normal_style))
    
    # Rozdział 2
    story.append(Paragraph("2. Nawigacja Lotnicza", heading_style))
    story.append(Paragraph("""
    Nawigacja lotnicza obejmuje określanie pozycji statku powietrznego i planowanie trasy lotu. 
    Podstawowe metody nawigacji to: nawigacja według punktów charakterystycznych (pilotaż), 
    nawigacja zliczeniowa, nawigacja radioelektroniczna oraz nawigacja satelitarna (GPS).
    """, normal_style))
    
    story.append(Paragraph("""
    Współrzędne geograficzne wyrażane są w stopniach, minutach i sekundach szerokości 
    i długości geograficznej. Magnesja magnetyczna różni się od geograficznej o wartość 
    deklinacji magnetycznej, która zmienia się w zależności od miejsca na Ziemi.
    """, normal_style))
    
    # Rozdział 3
    story.append(Paragraph("3. Meteorologia Lotnicza", heading_style))
    story.append(Paragraph("""
    Warunki meteorologiczne mają decydujący wpływ na bezpieczeństwo lotu. Pilot musi znać 
    i umieć interpretować prognozy pogody, raporty METAR i TAF. Podstawowe elementy pogody 
    to: ciśnienie, temperatura, wilgotność, wiatr, widoczność i zachmurzenie.
    """, normal_style))
    
    story.append(Paragraph("""
    METAR to zakodowany raport z obserwacji meteorologicznych na lotnisku. Przykład: 
    EPWA 281800Z 25015KT 9999 FEW035 SCT100 15/08 Q1021 NOSIG oznacza raport z Warszawy 
    z wiatrem 250° 15 węzłów, widocznością powyżej 10 km, zachmurzeniem FEW na 3500 ft.
    """, normal_style))
    
    # Rozdział 4
    story.append(Paragraph("4. Przepisy Lotnicze", heading_style))
    story.append(Paragraph("""
    Organizacja Międzynarodowego Lotnictwa Cywilnego (ICAO) ustala międzynarodowe standardy 
    i zalecane praktyki. W Polsce lotnictwo cywilne reguluje Ustawa Prawo lotnicze oraz 
    rozporządzenia wykonawcze. Każdy pilot musi posiadać odpowiednie licencje i uprawnienia.
    """, normal_style))
    
    story.append(Paragraph("""
    Podstawowe licencje pilota to: licencja pilota samolotów turystycznych (LAPL), 
    licencja pilota prywatnego (PPL), licencja pilota zawodowego (CPL) oraz licencja 
    pilota linii lotniczych (ATPL). Każda licencja wymaga określonej liczby godzin nalotu 
    i zdania odpowiednich egzaminów.
    """, normal_style))
    
    # Rozdział 5
    story.append(Paragraph("5. Systemy Statku Powietrznego", heading_style))
    story.append(Paragraph("""
    Nowoczesny samolot składa się z wielu systemów: napędowego, hydraulicznego, 
    elektrycznego, avioniki, klimatyzacji, przeciwoblodzeniowego i innych. Każdy system 
    ma swoje procedury normalne, nienormalne i awaryjne opisane w instrukcji eksploatacji.
    """, normal_style))
    
    story.append(Paragraph("""
    System avioniki obejmuje: autopilota, radar meteorologiczny, transponder, 
    radiostacje, systemy nawigacyjne (GPS, VOR, DME, ILS) oraz systemy ostrzegania 
    o zagrożeniach (TCAS, GPWS). Współczesne samoloty wyposażone są w szklane kokpity 
    z wielofunkcyjnymi wyświetlaczami.
    """, normal_style))
    
    # Stopka
    story.append(Spacer(1, 50))
    story.append(Paragraph("Dokument wygenerowany automatycznie przez Aero-Chat", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, 
                                       alignment=TA_CENTER)))
    
    # Zbuduj PDF
    doc.build(story)
    
    print(f"Przykładowy PDF utworzony: {filename}")
    return filename

if __name__ == "__main__":
    create_sample_pdf()
