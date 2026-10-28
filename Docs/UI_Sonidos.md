# Sonidos de interfaz (lista para encargar/componer)

Todos pasan por `UIEvents.Play(UISound.X)` (Scripts/Ui/UIEvents.cs). Hoy solo OpenMenu/CloseMenu suenan (SfxPlayer); el resto son ganchos.
Estilo: materiales reales y suaves (papel, lápiz, pincel, madera); sin bips electrónicos. Cortos, discretos.

| UISound | Cuándo suena | Idea |
|---|---|---|
| OpenMenu / CloseMenu | pausa, diálogo, diario | página que se abre / se cierra |
| Hover | ratón sobre un botón (`UIButtonSound`) | roce de lápiz muy leve |
| Select | foco con teclado/mando (`UIButtonSound`) | toque de lápiz sobre papel |
| Confirm | clic o Submit en un botón (`UIButtonSound`) | pincelada corta / sello |
| Cancel | (sin usar aún) volver atrás | papel arrugándose suave |
| PageTurn | diálogo avanza, diario cambia de página | pasar página |
| Notification | nueva notificación (`Notifications.Add`) | campanilla de madera suave |
| Interaction | interactuar con un objeto (`Hud`) | toque corto de madera |
| LoadingStart / LoadingBrush / LoadingComplete | pantalla de carga (SceneLoader) | pincel sobre lienzo, final con suspiro |
