namespace TheLivingCanvas.Save
{
    /// <summary>Componente con estado que entra en la partida guardada. Lo encuentra <see cref="SaveManager"/> por sí solo.</summary>
    public interface ISaveable
    {
        /// <summary>Copia el estado actual a <paramref name="data"/>.</summary>
        void WriteSave(SaveData data);

        /// <summary>Aplica lo guardado (solo se llama si hay partida). Debe refrescar la UI, sin avisos de ganancia ni celebraciones.</summary>
        void ReadSave(SaveData data, SaveRegistry registry);
    }
}
