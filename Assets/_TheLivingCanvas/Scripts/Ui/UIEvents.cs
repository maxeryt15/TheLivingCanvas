using System;
using TheLivingCanvas.Audio;
using UnityEngine;

namespace TheLivingCanvas.Ui
{
    /// <summary>Sonidos de interfaz que la UI anuncia; el audio se engancha a <see cref="UIEvents.Sound"/>.</summary>
    public enum UISound { OpenMenu, CloseMenu, Hover, Select, Confirm, Cancel, PageTurn, Notification, Interaction, LoadingStart, LoadingBrush, LoadingComplete }

    /// <summary>
    /// Punto único de eventos de sonido de la UI. La UI llama a Play(...) y no sabe qué suena: hoy solo
    /// abrir/cerrar menú tienen sonido (SfxPlayer); el resto son ganchos listos para papel, lápiz, pincel, madera...
    /// </summary>
    public static class UIEvents
    {
        public static event Action<UISound> Sound;

        public static void Play(UISound sound) => Sound?.Invoke(sound);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Init()
        {
            Sound = null; // con "Enter Play Mode Options" sin recarga de dominio no se duplican suscripciones
            Sound += Bridge;
        }

        static void Bridge(UISound s)
        {
            switch (s)
            {
                case UISound.OpenMenu: SfxPlayer.Play(Sfx.UiOpen); break;
                case UISound.CloseMenu: SfxPlayer.Play(Sfx.UiClose); break;
            }
        }
    }
}
