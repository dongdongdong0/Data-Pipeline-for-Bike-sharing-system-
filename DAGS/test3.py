from kafka import KafkaProducer
from kafka import KafkaConsumer

producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
messages = [b'Message 1', b'Message 2', b'Message 3', b'Message 4']
for msg in messages:
    producer.send('test_topic', msg)
    producer.flush()
print("All messages sent")




consumer = KafkaConsumer(
    'test_topic',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest'
)
message_count = 0
max_messages = 3

for message in consumer:
    print(f"Received message: {message.value.decode('utf-8')}")
    message_count += 1
    print(f"Message count: {message_count}")  # 显示当前消息计数
    if message_count >= max_messages:
        print("Reached max messages, breaking out of loop.")
        break
