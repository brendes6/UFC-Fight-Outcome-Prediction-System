
export const getPredictions = async (fighter1, fighter2) => {
  const SERVICE_URL = "https://ufc-predictions-685306641609.us-central1.run.app/predict";
  
  try {
    const response = await fetch(SERVICE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        red_fighter: fighter1,
        blue_fighter: fighter2,
      }),
    });
    console.log(response);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Prediction failed");
    }

    const data = await response.json();
    console.log("Prediction:", data);
    return data;
  } catch (error) {
    console.error("Error fetching prediction:", error);
    return null;
  }
};

export const getUpcoming = async () => {
  try {
    const response = await fetch(
      `https://ufc-predictor.fly.dev/upcoming`
    );

    if (!response.ok) {
      throw new Error("API error: " + response.statusText);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching prediction:", error);
    return null;
  }
};
