from django.shortcuts import render
from django.http import HttpResponse
from .lichess_data import LichessData
from .forms import LichessForm

# Create your views here.

def home(request):
    return render(request,'blog/home.html')
    #return HttpResponse("Hello, Django!")

def about(request):
    return render(request,'blog/about.html')

def lichess_view(request):
    result_html = None
    total_result_html = None
    error_message = None
    if request.method=="POST":
        form = LichessForm(request.POST)
        #username= str(request.POST.get("username","Fearghal97"))
        #number_of_games = int(request.POST.get("number_of_games",0))
        #gamemode = str(request.POST.get("gamemode","all")).lower()
        if form.is_valid():
            username = form.cleaned_data["username"]
            gamemode = form.cleaned_data["gamemode"]
            number_of_games = form.cleaned_data["number_of_games"]
            opening = form.cleaned_data["opening"]
            personal_token= form.cleaned_data["personal_token"]
            if personal_token!="":
                try:
                    lichess_data=LichessData(username,number_of_games,gamemode,opening,personal_token)
                    sample_result,lichess_df,total_results_df = lichess_data.run_everything() # This is a dataframe

                    #sample_result=sample_result.reset_index(drop=True)
                    #result = sample_result.to_dict(orient="records")[0] 
                    #result = sample_result.iloc[0].to_dict()

                    result_html = sample_result.to_html(
                        classes="table table-striped table-bordered",  # Bootstrap styling
                        index=False,  # hides the index column if you don’t need it
                        justify="center"  # aligns table nicely
                    )

                    total_result_html = total_results_df.to_html(
                        classes="table table-striped table-bordered",  # Bootstrap styling
                        index=False,  # hides the index column if you don’t need it
                        justify="center"  # aligns table nicely
                    )
                #sample_results 
                except:
                    print (lichess_data.error_message)
                    if lichess_data.error_message:
                        error_message=lichess_data.error_message
                    else:
                        error_message="Unknown Error"
            else:
                form = LichessForm()

    else:
        form = LichessForm()

    context = {
        "form": form,
        "table":result_html,
        "total_table":total_result_html,
        "error": error_message
        }

    return render(request, "blog/lichess_info.html",context)

def lichess_games(request):
    result_html = None
    if request.method=="POST":
        username= str(request.POST.get("username","Fearghal97"))
        number_of_games = int(request.POST.get("number_of_games",0))
        gamemode = str(request.POST.get("gamemode","all")).lower()
        lichess_data=LichessData(username,number_of_games,gamemode)
        
        sample_result,lichess_df,total_results_df = lichess_data.run_everything() # This is a dataframe
        #sample_result=sample_result.reset_index(drop=True)
        #result = sample_result.to_dict(orient="records")[0] 
        #result = sample_result.iloc[0].to_dict()
        result_html = total_results_df.to_html(
            classes="table table-striped table-bordered",  # Bootstrap styling
            index=False,  # hides the index column if you don’t need it
            justify="center"  # aligns table nicely
        )

        #sample_results 

    return render(request, "blog/lichess_results.html",{"table":result_html})