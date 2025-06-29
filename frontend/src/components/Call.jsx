

export const getPredictions = async (fighter1, fighter2) => {
  try {
    const response = await fetch(
      `https://ufc-predictor.fly.dev/predict?fighter1=${encodeURIComponent(fighter1)}&fighter2=${encodeURIComponent(fighter2)}`
    );

    if (!response.ok) {
      throw new Error("API error: " + response.statusText);
    }

    const data = await response.json();
    console.log("Prediction:", data);
    return data;
  } catch (error) {
    console.error("Error fetching prediction:", error);
    return null;
  }
};
