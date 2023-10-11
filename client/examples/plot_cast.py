import sys
from neslter.api import Client 


def plot_cast(df, var, title):
    import matplotlib.pyplot as plt

    # Create the line graph with pressure on the y-axis and inverted
    plt.figure(figsize=(4.5, 8))
    plt.plot(df[var], df['prdm'], c='blue', linestyle='-')
    plt.ylabel('Pressure (prdm)')
    plt.xlabel(f'{var}')
    plt.title(title)
    plt.gca().invert_yaxis() # invert y-axis so that pressure increases downward
    plt.grid(True)
    plt.show()


def main(asc_path):
    client = Client()

    df = client.parse_asc(asc_path)

    plot_cast(df, var='sal00', title='Salinity (sal00) vs Pressure (prdm)')


if __name__ == '__main__':
    asc_path = sys.argv[1]
    main(asc_path)
