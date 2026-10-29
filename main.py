from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
import re

Window.clearcolor = (0.96, 0.96, 0.96, 1)

C_BG = (0.96, 0.96, 0.96, 1)
C_CARD = (1.0, 1.0, 1.0, 1)
C_INPUT = (0.90, 0.90, 0.90, 1)
C_TEXT = (0.1, 0.1, 0.1, 1)
C_MUTED = (0.4, 0.4, 0.4, 1)
C_ACCENT = (0.0, 0.47, 1.0, 1)
C_SUCCESS = (0.2, 0.8, 0.35, 1)
C_DANGER = (1.0, 0.23, 0.18, 1)
C_RESULT = (0.0, 0.2, 0.6, 1)
C_PROCESS = (0.1, 0.1, 0.1, 1)

SUPER = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5',
         '⁶':'6','⁷':'7','⁸':'8','⁹':'9','⁻':'-'}

def limpiar_superindices(t):
    return re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+',
                  lambda m: '^' + ''.join(SUPER[c] for c in m.group(0)), t)

def parsear(texto):
    if not texto or not texto.strip(): raise ValueError("Vacío")
    s = limpiar_superindices(texto.strip())
    s = re.sub(r'([xyz])(\d+)', r'\1^\2', s)
    s = s.replace(" ", "").replace("−", "-").replace("–", "-").replace("×", "*").lower()
    s = re.sub(r'(?<!^)-', '+-', s)
    if s.startswith('+'): s = s[1:]
    terminos = [t for t in s.split('+') if t]
    if not terminos: raise ValueError("Sin términos")
    
    diccionario = {}
    for t in terminos:
        signo = -1.0 if t.startswith('-') else 1.0
        if t[0] in '+-': t = t[1:]
        
        match_num = re.match(r'^(\d*\.?\d*)', t)
        num_str = match_num.group(1)
        coef = float(num_str) if num_str not in ('', '.') else 1.0
        coef *= signo
        
        vars_str = t[match_num.end():]
        exp_x = exp_y = exp_z = 0
        
        if vars_str:
            partes = re.findall(r'([xyz])(?:\^(\d+))?', vars_str)
            for letra, exp in partes:
                e = int(exp) if exp else 1
                if letra == 'x': exp_x += e
                elif letra == 'y': exp_y += e
                elif letra == 'z': exp_z += e
            
            reconstruido = "".join(f"{letra}{'^'+exp if exp else ''}" for letra, exp in partes)
            if reconstruido != vars_str:
                raise ValueError(f"Término inválido: '{t}'")
        
        clave = (exp_x, exp_y, exp_z)
        diccionario[clave] = diccionario.get(clave, 0.0) + coef
    return diccionario

def fmt_num(x):
    if abs(x - round(x)) < 1e-9: return str(int(round(x)))
    return f"{x:g}"

def fmt_termino(coef, tupla_exp):
    if abs(coef) < 1e-12: return "0"
    ex, ey, ez = tupla_exp
    cs = fmt_num(abs(coef))
    cuerpo = ""
    if ex > 0:
        e = str(ex).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
        cuerpo += "x" + (e if ex > 1 else "")
    if ey > 0:
        e = str(ey).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
        cuerpo += "y" + (e if ey > 1 else "")
    if ez > 0:
        e = str(ez).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
        cuerpo += "z" + (e if ez > 1 else "")
    
    if not cuerpo: return ("-" if coef < 0 else "") + cs
    if cs == "1": return ("-" if coef < 0 else "") + cuerpo
    return ("-" if coef < 0 else "") + cs + cuerpo

class Polinomio:
    def __init__(self, dic):
        self.dic = {k: v for k, v in dic.items() if abs(v) > 1e-12}
    
    def __str__(self):
        if not self.dic: return "0"
        claves = sorted(self.dic.keys(), key=lambda k: (k[0]+k[1]+k[2], k[0], k[1], k[2]), reverse=True)
        partes = [fmt_termino(self.dic[k], k) for k in claves]
        res = partes[0]
        for p in partes[1:]:
            if p.startswith("-"): res += " - " + p[1:]
            else: res += " + " + p
        return res
    
    def suma(self, o):
        nuevo = dict(self.dic)
        for k, v in o.dic.items(): nuevo[k] = nuevo.get(k, 0.0) + v
        return Polinomio(nuevo)
    
    def resta(self, o):
        nuevo = dict(self.dic)
        for k, v in o.dic.items(): nuevo[k] = nuevo.get(k, 0.0) - v
        return Polinomio(nuevo)
    
    def multiplicacion(self, o):
        nuevo = {}
        for k1, v1 in self.dic.items():
            for k2, v2 in o.dic.items():
                k = (k1[0]+k2[0], k1[1]+k2[1], k1[2]+k2[2])
                nuevo[k] = nuevo.get(k, 0.0) + (v1 * v2)
        return Polinomio(nuevo)

def render_columna_paso_a_paso(p, q, nom_p="P", nom_q="Q"):
    todos_k = set(p.dic.keys()) | set(q.dic.keys())
    if not todos_k: return "Ambos son cero."
    max_x = max(k[0] for k in todos_k); max_y = max(k[1] for k in todos_k); max_z = max(k[2] for k in todos_k)
    columnas = []
    for ex in range(max_x, -1, -1):
        for ey in range(max_y, -1, -1):
            for ez in range(max_z, -1, -1):
                columnas.append((ex, ey, ez))
                
    res_pol = p.multiplicacion(q)
    claves_q = sorted(q.dic.keys(), key=lambda k: (k[0]+k[1]+k[2], k[0], k[1], k[2]))
    parciales = []
    for kq in claves_q:
        vq = q.dic[kq]
        if abs(vq) < 1e-12: continue
        dic_parcial = {}
        for kp, vp in p.dic.items():
            k = (kp[0]+kq[0], kp[1]+kq[1], kp[2]+kq[2])
            dic_parcial[k] = dic_parcial.get(k, 0.0) + (vp * vq)
        parciales.append(Polinomio(dic_parcial))
        
    anchos = []
    for col in columnas:
        term_p = fmt_termino(p.dic[col], col) if col in p.dic else ""
        term_q = fmt_termino(q.dic[col], col) if col in q.dic else ""
        term_r = fmt_termino(res_pol.dic[col], col) if col in res_pol.dic else ""
        parciales_terms = [fmt_termino(par.dic[col], col) for par in parciales if col in par.dic]
        max_len = max([len(term_p), len(term_q), len(term_r)] + [len(t) for t in parciales_terms] + [3])
        anchos.append(max_len)
        
    def render_fila(dic):
        celdas = []
        for i, col in enumerate(columnas):
            if col in dic and abs(dic[col]) > 1e-12:
                c = dic[col]
                term = fmt_termino(abs(c), col)
                if c > 0 and any(celdas): term = "+ " + term
                elif c < 0: term = "- " + term
                celdas.append(term.rjust(anchos[i]))
            else: celdas.append("".rjust(anchos[i]))
        return "".join(celdas).rstrip()
        
    lineas_render = [render_fila(p.dic), render_fila(q.dic)]
    ancho_max = max(len(l) for l in lineas_render)
    for par in parciales:
        l_par = render_fila(par.dic)
        lineas_render.append(l_par)
        ancho_max = max(ancho_max, len(l_par))
        
    linea_res = render_fila(res_pol.dic)
    ancho_max = max(ancho_max, len(linea_res))
    
    lineas_finales = [lineas_render[0].rjust(ancho_max), lineas_render[1].rjust(ancho_max)]
    raya = "─" * ancho_max
    lineas_finales.append(raya)
    for i in range(2, len(lineas_render)): lineas_finales.append(lineas_render[i].rjust(ancho_max))
    lineas_finales.append(raya)
    lineas_finales.append(linea_res.rjust(ancho_max))
    
    return "\n".join(lineas_finales)

def evaluar_expresion(expr, polis):
    expr = expr.upper()
    letras_usadas = set(re.findall(r'[A-Z]', expr))
    for l in letras_usadas:
        if l not in polis: raise ValueError(f"El polinomio '{l}' no está definido.")
    entorno = {l: polis[l] for l in letras_usadas}
    
    class PWrapper:
        def __init__(self, p): self.p = p
        def __add__(self, o): return PWrapper(self.p.suma(o.p if isinstance(o, PWrapper) else Polinomio({(0,0,0): o})))
        def __radd__(self, o): return self.__add__(o)
        def __sub__(self, o): return PWrapper(self.p.resta(o.p if isinstance(o, PWrapper) else Polinomio({(0,0,0): o})))
        def __rsub__(self, o): return PWrapper(Polinomio({(0,0,0): o}).resta(self.p))
        def __mul__(self, o): return PWrapper(self.p.multiplicacion(o.p if isinstance(o, PWrapper) else Polinomio({(0,0,0): o})))
        def __rmul__(self, o): return self.__mul__(o)
        def __str__(self): return str(self.p)

    entorno_wrap = {k: PWrapper(v) for k, v in entorno.items()}
    try: res = eval(expr, {"__builtins__": None}, entorno_wrap)
    except Exception as e: raise ValueError(f"Expresión inválida: {e}")
    
    if isinstance(res, PWrapper): return res.p
    if isinstance(res, (int, float)): return Polinomio({(0,0,0): res})
    raise ValueError("El resultado no es un polinomio válido.")

class CalculadoraKivy(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.filas_polinomios = []
        self.tab_actual = "res"

        # Ya no hay ScrollView principal, la pantalla es fija
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.add_widget(self.layout)

        self.layout.add_widget(Label(text="Calculadora Polinomios", font_size='24sp', size_hint_y=None, height=50, color=C_TEXT))

        card1 = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        card1.bind(minimum_height=card1.setter('height'))
        card1.add_widget(Label(text="1. Polinomios", size_hint_y=None, height=30, color=C_MUTED))
        
        self.contenedor_pol = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.contenedor_pol.bind(minimum_height=self.contenedor_pol.setter('height'))
        card1.add_widget(self.contenedor_pol)
        
        btn_herr = GridLayout(cols=2, size_hint_y=None, height=45, spacing=5)
        btn_add = Button(text="+ Polinomio", background_color=C_ACCENT)
        btn_add.bind(on_press=self.agregar_fila)
        btn_herr.add_widget(btn_add)
        btn_pot = Button(text="^ (Potencia)", background_color=C_INPUT, color=C_TEXT)
        btn_pot.bind(on_press=self.insertar_potencia)
        btn_herr.add_widget(btn_pot)
        card1.add_widget(btn_herr)
        self.layout.add_widget(card1)

        card2 = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        card2.bind(minimum_height=card2.setter('height'))
        card2.add_widget(Label(text="2. Operación", size_hint_y=None, height=30, color=C_MUTED))
        
        self.entry_expr = TextInput(text="P * Q", multiline=False, size_hint_y=None, height=50, font_size='18sp', halign='center', background_color=C_INPUT, foreground_color=C_SUCCESS)
        card2.add_widget(self.entry_expr)

        grid_teclado = GridLayout(cols=7, size_hint_y=None, height=45, spacing=2)
        for txt in ["+", "-", "*", "/", "(", ")", "C"]:
            btn = Button(text=txt, background_color=C_INPUT, color=C_TEXT)
            btn.bind(on_press=lambda instance, t=txt: self.agregar_a_expresion(t))
            grid_teclado.add_widget(btn)
        card2.add_widget(grid_teclado)

        self.frame_letras = GridLayout(cols=5, size_hint_y=None, spacing=5)
        self.frame_letras.bind(minimum_height=self.frame_letras.setter('height'))
        card2.add_widget(self.frame_letras)

        btn_calc = Button(text="Calcular", size_hint_y=None, height=50, background_color=C_SUCCESS, font_size='20sp')
        btn_calc.bind(on_press=self.calcular)
        card2.add_widget(btn_calc)
        self.layout.add_widget(card2)

        # Aquí la tarjeta 3 ocupa el espacio restante de la pantalla
        card3 = BoxLayout(orientation='vertical', size_hint_y=1, spacing=5)
        card3.add_widget(Label(text="3. Resultado", size_hint_y=None, height=30, color=C_MUTED))
        
        tabs = GridLayout(cols=2, size_hint_y=None, height=45, spacing=5)
        self.btn_tab_res = Button(text="Resultado", background_color=C_ACCENT)
        self.btn_tab_res.bind(on_press=lambda x: self.cambiar_tab("res"))
        self.btn_tab_proc = Button(text="Proceso", background_color=C_INPUT, color=C_TEXT)
        self.btn_tab_proc.bind(on_press=lambda x: self.cambiar_tab("proc"))
        tabs.add_widget(self.btn_tab_res)
        tabs.add_widget(self.btn_tab_proc)
        card3.add_widget(tabs)

        # Contenedor de las cajas de texto con ScrollView
        self.contenedor_tabs = BoxLayout(size_hint_y=1)
        
        self.scroll_res = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=5)
        self.lbl_res = Label(text="", size_hint_y=None, halign="left", valign="top", color=C_RESULT, font_size='15sp')
        self.lbl_res.bind(texture_size=self.lbl_res.setter('size'))
        self.lbl_res.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.scroll_res.add_widget(self.lbl_res)
        
        self.scroll_proc = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=5)
        self.lbl_proc = Label(text="", size_hint_y=None, halign="left", valign="top", color=C_PROCESS, font_size='15sp', font_name='RobotoMono-Regular')
        self.lbl_proc.bind(texture_size=self.lbl_proc.setter('size'))
        self.lbl_proc.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.scroll_proc.add_widget(self.lbl_proc)
        
        self.contenedor_tabs.add_widget(self.scroll_res)
        card3.add_widget(self.contenedor_tabs)
        
        self.layout.add_widget(card3)

        self.agregar_fila()
        self.agregar_fila()

    def insertar_potencia(self, instance):
        self.entry_expr.text += "^"

    def agregar_a_expresion(self, txt):
        if txt == "C":
            self.entry_expr.text = ""
        else:
            self.entry_expr.text += f" {txt} "

    def cambiar_tab(self, tab):
        self.tab_actual = tab
        self.contenedor_tabs.clear_widgets()
        if tab == "res":
            self.btn_tab_res.background_color = C_ACCENT
            self.btn_tab_proc.background_color = C_INPUT
            self.contenedor_tabs.add_widget(self.scroll_res)
        else:
            self.btn_tab_proc.background_color = C_ACCENT
            self.btn_tab_res.background_color = C_INPUT
            self.contenedor_tabs.add_widget(self.scroll_proc)

    def agregar_fila(self, *args):
        if len(self.filas_polinomios) >= 8: return
        
        letras_usadas = [f['letra'].text for f in self.filas_polinomios]
        letra_sug = next((c for c in "PQRSTUVWXYZ" if c not in letras_usadas), "A")
        
        fila = BoxLayout(size_hint_y=None, height=45, spacing=5)
        
        ent_letra = TextInput(text=letra_sug, multiline=False, size_hint_x=0.15, halign='center', background_color=C_INPUT, foreground_color=C_ACCENT)
        ent_letra.bind(text=self.actualizar_letras)
        fila.add_widget(ent_letra)
        
        lbl_igual = Label(text="=", size_hint_x=0.05, color=C_TEXT)
        fila.add_widget(lbl_igual)
        
        ent_poli = TextInput(multiline=False, size_hint_x=0.65, background_color=C_INPUT, foreground_color=C_TEXT)
        fila.add_widget(ent_poli)
        
        btn_del = Button(text="X", size_hint_x=0.15, background_color=C_DANGER)
        btn_del.bind(on_press=lambda x: self.eliminar_fila(fila))
        fila.add_widget(btn_del)
        
        self.contenedor_pol.add_widget(fila)
        self.filas_polinomios.append({'layout': fila, 'letra': ent_letra, 'poli': ent_poli})
        self.actualizar_letras()

    def eliminar_fila(self, fila):
        for f in self.filas_polinomios:
            if f['layout'] == fila:
                self.contenedor_pol.remove_widget(fila)
                self.filas_polinomios.remove(f)
                break
        self.actualizar_letras()

    def actualizar_letras(self, *args):
        self.frame_letras.clear_widgets()
        letras = [f['letra'].text.strip().upper() for f in self.filas_polinomios if f['letra'].text.strip()]
        for l in letras:
            btn = Button(text=l, size_hint_y=None, height=40, background_color=C_ACCENT)
            btn.bind(on_press=lambda instance, letra=l: self.agregar_a_expresion(f" {letra} "))
            self.frame_letras.add_widget(btn)

    def calcular(self, instance):
        polis = {}
        try:
            for f in self.filas_polinomios:
                letra = f['letra'].text.strip().upper()
                texto = f['poli'].text.strip()
                if not letra or not texto: continue
                if len(letra) != 1 or not letra.isalpha(): raise ValueError(f"Letra inválida: '{letra}'")
                polis[letra] = Polinomio(parsear(texto))
            
            if not polis: raise ValueError("Ingresa al menos un polinomio.")
            
            expr = self.entry_expr.text.strip()
            r = evaluar_expresion(expr, polis)
            
            salida = "Polinomios ingresados:\n"
            letras_expr = set(re.findall(r'[A-Z]', expr.upper()))
            for letra in letras_expr:
                if letra in polis: salida += f"  {letra} = {polis[letra]}\n"
            
            salida += f"\nOperación: {expr}\n"
            salida += "─" * 30 + "\n"
            salida += f"Resultado = {r}\n"
            
            match_mult = re.fullmatch(r'\s*([A-Z])\s*\*\s*([A-Z])\s*', expr.upper())
            if match_mult:
                l1, l2 = match_mult.groups()
                if l1 in polis and l2 in polis:
                    salida += "\nProceso en columna:\n\n"
                    salida += render_columna_paso_a_paso(polis[l1], polis[l2], l1, l2)

            self.lbl_res.text = f"Operación: {expr}\n\n= {r}\n\n{'─'*35}\nPolinomios:\n" + "\n".join(f"{k} = {v}" for k, v in polis.items())
            self.lbl_proc.text = salida
            
            self.cambiar_tab("proc")

        except Exception as e:
            self.lbl_res.text = f"Error:\n{str(e)}"
            self.lbl_proc.text = f"Error:\n{str(e)}"
            self.cambiar_tab("res")

class MiCalculadoraApp(App):
    def build(self):
        self.title = "PolyMath v1.0.0"
        return CalculadoraKivy()

if __name__ == '__main__':
    MiCalculadoraApp().run()