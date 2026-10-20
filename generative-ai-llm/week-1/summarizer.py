"""Local Hugging Face summarizer; first run may download model weights."""
def summarize(text: str, max_words: int = 80) -> str:
    text=text.strip()
    if not text: return "Please enter text to summarize."
    if len(text)>20000: return "Input is too long (limit: 20,000 characters)."
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("Install transformers and torch to run the summarizer.") from exc
    model=pipeline('summarization',model='sshleifer/distilbart-cnn-12-6')
    result=model(text,max_length=max(20,min(180,max_words*2)),min_length=10,do_sample=False,truncation=True)
    return result[0]['summary_text']
if __name__=='__main__':
    sample=input('Text to summarize: ')
    print(summarize(sample))
