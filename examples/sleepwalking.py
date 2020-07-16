import time

def main():
	for i in range(5):
		print(f"dormi {i}")
		time.sleep(5)
		print("acordei")

if(__name__=='__main__'):
	main()