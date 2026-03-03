import mlflow.sklearn
import pandas as pd

mlflow.set_tracking_uri("http://localhost:5000")

model = mlflow.sklearn.load_model(
    "models:/MultinomialNB/Production"
)

input_data = pd.DataFrame({
    "comment_text": ["As a local person I can say this and be honest that is it local culture that has gotten us to where we are with hpd and local culture is not going to get us out of this mess.  I feel the same way about how the DOE is looking at mainland candidates. Unfortunately hpd is known around the nation for one thing.  Sex with prostitutes for investigative purposes.  How embarrassing that the good job that so many officers perform every day gets overshadowed by scandal after scandal. It will be a learning process for someone from the mainland so they will need to open to learning and we will have to teach them about Hawaii. But we also need to be open to be taught as we might learn some better ways to run things and clean things up."]
})

prediction = model.predict(input_data)
proba = model.predict_proba(input_data)

print("Prediction:", prediction)
print("Probability:", proba[:, 1])