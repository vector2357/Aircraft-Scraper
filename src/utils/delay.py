def delay (seconds: float):
    """Função para criar um delay/sleep por um número especificado de segundos."""
    import time
    print(f"⏰ Aguardando {seconds:.1f} segundos...")
    time.sleep(seconds)