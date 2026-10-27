namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Importancia de un interactuable cuando varios coinciden en la mirada: se muestra solo el de mayor valor.
    /// Para añadir un tipo nuevo, inserta un valor con el número que le corresponda entre los existentes.
    /// </summary>
    public enum InteractionPriority
    {
        Environmental = 0, // puertas, interruptores...
        Examine = 10,      // observar un objeto (valor por defecto de IInteractable)
        Dialogue = 20,     // hablar con un NPC
        Artwork = 30,      // cuadros y lienzos importantes
        Narrative = 40,    // interacción clave de la historia
    }

    /// <summary>Opcional: un IInteractable que lo implementa declara su prioridad; si no, es Examine.</summary>
    public interface IInteractionPriority
    {
        InteractionPriority Priority { get; }
    }
}
