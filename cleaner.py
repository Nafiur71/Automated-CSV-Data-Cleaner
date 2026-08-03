import pandas as pd

def clean_my_data(file_path):
    print("file is loading")
    df=pd.read_csv(file_path)
    print("main data")
    print(df.to_string(index=False))

    # remove doublicate values from the data sheet
    df=df.drop_duplicates()
    
    # missing valu to defoult value ;
    df['Age']= df['Age'].fillna(25)
    df['Salary']= df['Salary'].fillna(35000)
    print("Data cleanning is compelete ")
    print("Printing clean data ")
    print(df.to_string(index=False))
    output_file="cleaned_data.csv"
    df.to_csv(output_file,index=False)
    print(f"\n💾 New file saved successfully: {output_file}")


clean_my_data("dirty_data.csv")
