def engine_left_time(tbo, horas_atual):
    """
    Calcula as horas restantes do motor até o próximo TBO (Time Between Overhaul)
    
    Args:
        tbo: Horas totais do TBO (ex: 2000)
        horas_atual: Horas atuais do motor (ex: 857)
    
    Returns:
        Horas restantes até o próximo TBO
    """
    try:
        # Converter para float, removendo vírgulas se existirem
        tbo_float = float(str(tbo).replace(',', ''))
        horas_float = float(str(horas_atual).replace(',', ''))
        
        # O cálculo correto é TBO - horas atuais
        horas_restantes = tbo_float - horas_float
        
        # Garantir que não retorne negativo (se horas > TBO, retorna 0)
        if horas_restantes < 0:
            print(f"⚠️ Aviso: Horas atuais ({horas_float}) excedem TBO ({tbo_float})")
            return '0'
        
        return f"{horas_restantes:.2f}"
        
    except (ValueError, TypeError) as e:
        print(f"🚨 Erro ao calcular horas restantes: TBO={tbo}, Horas={horas_atual}, Erro={e}")
        return '0'