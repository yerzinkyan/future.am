# Օգտագործում ենք Python-ի պաշտոնական թեթև տարբերակը
FROM python:3.11-slim

# Սահմանում ենք միջավայրի փոփոխականներ, որ Python-ն ավելի արագ և ճիշտ աշխատի Docker-ում
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Սահմանում ենք աշխատանքային պանակը կոնտեյների ներսում
WORKDIR /app

# Պատճենում ենք միայն պահանջվող գրադարանների ցանկը (քեշավորումն օպտիմալացնելու համար)
COPY requirements.txt .

# Տեղադրում ենք կախվածությունները
RUN pip install --no-cache-dir -r requirements.txt

# Պատճենում ենք նախագծի ամբողջ կոդը
COPY . .

# Բաց ենք թողնում 7070 պորտը
EXPOSE 7070

# Գործարկում ենք ծրագիրը Gunicorn արտադրական սերվերով (4 worker-ներով)
CMD ["gunicorn", "--bind", "0.0.0.0:7070", "--workers", "4", "app:app"]